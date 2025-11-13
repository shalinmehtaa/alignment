# AI Alignment Sandbox

Code, prompts, and data for running AI alignment evaluations across multiple language models using Petri.

## Setup

1. Clone this repository and the Petri framework side by side:

```bash
git clone https://github.com/shalinmehtaa/alignment.git
git clone https://github.com/kaifronsdal/petri.git
cd alignment
```

2. Install dependencies using [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

3. Create a `.env` file with your API keys:

```bash
OPENROUTER_API_KEY=your_key_here
```

## Running Experiments

Run evaluations on any model via OpenRouter:

```bash
# Baseline evaluation
uv run python run_eval.py --target-model openrouter/MODEL_NAME --scenario-family baseline

# Specialized scenarios
uv run python run_eval.py --target-model openrouter/MODEL_NAME --scenario-family cyber

uv run python run_eval.py --target-model openrouter/MODEL_NAME --scenario-family influence

uv run python run_eval.py --target-model openrouter/MODEL_NAME --scenario-family geopolitics
```

## Reproducing Analysis

Open the analysis notebooks:

```bash
# Baseline analysis
uv run jupyter notebook analysis_baseline.ipynb

# Specialized scenario analysis
uv run jupyter notebook analysis_china.ipynb
```

## Data Structure

- `instructions.py` - Scenario definitions and custom metric dimensions
- `run_eval.py` - Evaluation script
- `*-baseline/` - Raw transcript data from baseline evaluations
- `*-cyber/` - Cybersecurity scenario transcripts
- `*-geopolitics/` - Geopolitical bias scenario transcripts
- `*-influence/` - Influence/manipulation scenario transcripts
- `analysis_*.ipynb` - Analysis notebooks with plotting code

## Study Details

This study used Petri version 0.1.0 with model versions accessed during the first two weeks of November 2025. Since models may change over time, results using current API endpoints may differ slightly.

