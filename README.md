# Multi-Market Bot Lab

Initial framework to design, test, and optimize simple strategies across multiple markets
(crypto, forex, equities, indices) with strict max drawdown control.

## Objective

- Define strategy specifications in Markdown.
- Download historical data (baseline: Dukascopy).
- Run an automated loop: development -> backtest -> optimization -> retry.
- Save iterative reports for audit and comparison.

## Structure

- `docs/` specifications and operational guidelines.
- `config/` instrument universe, timeframes, and risk constraints.
- `scripts/run_cycle.py` iterative loop orchestrator.
- `reports/` per-run JSON outputs.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python scripts/run_cycle.py --iterations 3
```

## Dukascopy Data Download

You can use `dukascopy-node` directly as described in the official documentation:

```bash
npx dukascopy-node -i eurusd -from 2024-01-01 -to 2024-12-31 -t m1 -f csv
```

To integrate data download into the automated loop, complete `ingest_data()` in
`scripts/run_cycle.py` based on your environment (local CLI or service).
