import argparse
import os
import json

from inspect_ai import eval as inspect_eval
from inspect_ai.model import get_model, GenerateConfig

from dotenv import load_dotenv

from petri.tasks.petri import AUDITOR_INSTRUCTIONS
from petri.scorers.judge import alignment_judge, DIMENSIONS

from china.instructions import (
    CYBER_SPECIAL_INSTRUCTIONS,
    INFLUENCE_SPECIAL_INSTRUCTIONS,
    GEOPOLITICS_SPECIAL_INSTRUCTIONS,
    CUSTOM_DIMENSIONS
)

load_dotenv()

ALL_DIMENSIONS = {**DIMENSIONS, **CUSTOM_DIMENSIONS}

CUSTOM_JUDGE = alignment_judge(dimensions=ALL_DIMENSIONS, retries=5)

# --- Scenario family selector ---

SCENARIO_FAMILIES = {
    "baseline": None,  # use default AUDITOR_INSTRUCTIONS
    "cyber": CYBER_SPECIAL_INSTRUCTIONS,
    "influence": INFLUENCE_SPECIAL_INSTRUCTIONS,
    "geopolitics": GEOPOLITICS_SPECIAL_INSTRUCTIONS,
}


def make_out_dir(target_model_id: str, scenario_family: str, out_root: str) -> str:
    """
    Construct an output directory of the form:
    <out_root>/<sanitized_model_id>-<scenario_family>
    """
    safe_model = (
        target_model_id.replace("openrouter/", "")
        .replace("/", "-")
        .replace(":", "_")
        .replace(" ", "_")
        
    )
    out_dir = os.path.join(out_root, f"{safe_model}-{scenario_family}")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def run_petri(
    target_model_id: str,
    scenario_family: str = "baseline",
    max_turns: int = 32,
    out_root: str = "./outputs",
):
    """
    Run Petri audit on a given target model via OpenRouter with optional
    scenario_family: 'baseline' | 'cyber' | 'influence' | 'geopolitics'.
    Output directory is derived from target_model_id + scenario_family
    under out_root.
    """

    if scenario_family not in SCENARIO_FAMILIES:
        raise ValueError(f"Unknown scenario_family: {scenario_family}")

    special_instructions = SCENARIO_FAMILIES[scenario_family]
    out_dir = make_out_dir(target_model_id, scenario_family, out_root)

    # Target via OpenRouter (uses OPENROUTER_API_KEY)
    target = get_model(
        target_model_id,
        config=GenerateConfig(max_tokens=4000),
    )

    # Auditor (OpenRouter OpenAI; keep under 8k limit)
    auditor = get_model(
        "openrouter/openai/gpt-5-mini",
        config=GenerateConfig(max_tokens=6000, reasoning_tokens=2000),
    )

    # Judge (OpenRouter Anthropic)
    judge = get_model(
        "openrouter/anthropic/claude-haiku-4.5",
        config=GenerateConfig(max_tokens=4000),
    )

    task_args = {
        "max_turns": max_turns,
        "transcript_save_dir": out_dir,
        "scorer": CUSTOM_JUDGE,
    }

    # Only override instructions if you picked a non-baseline scenario family
    if special_instructions is not None:
        # Petri's audit() expects `special_instructions` as a string resource
        # that can be treated as a file path or a JSON list-of-strings.
        if isinstance(special_instructions, list):
            # Write the instructions to a JSON file and pass the path so that
            # petri.tasks.petri.audit() can load it via `resource(...)`.
            special_path = os.path.join(
                out_dir,
                f"{scenario_family}_special_instructions.json",
            )
            with open(special_path, "w", encoding="utf-8") as f:
                json.dump(special_instructions, f, ensure_ascii=False, indent=2)
            task_args["special_instructions"] = special_path
        else:
            task_args["special_instructions"] = special_instructions

    inspect_eval(
        "petri/audit",
        model_roles={
            "target": target,
            "auditor": auditor,
            "judge": judge,
        },
        max_connections=32,
        max_retries=8,
        fail_on_error=5,
        task_args=task_args,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Petri audit via OpenRouter.")

    parser.add_argument(
        "--target-model",
        "-m",
        required=True,
        help="Target model id, e.g. 'openrouter/moonshotai/kimi-k2-thinking'",
    )
    parser.add_argument(
        "--scenario-family",
        "-s",
        choices=list(SCENARIO_FAMILIES.keys()),
        default="baseline",
        help="Scenario family to run: baseline | cyber | influence | geopolitics",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=16,
        help="Maximum number of turns per Petri conversation.",
    )
    parser.add_argument(
        "--out-root",
        default="./",
        help="Root directory under which per-run output dirs are created.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_petri(
        target_model_id=args.target_model,
        scenario_family=args.scenario_family,
        max_turns=args.max_turns,
        out_root=args.out_root,
    )
