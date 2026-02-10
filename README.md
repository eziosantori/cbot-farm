# Multi-Market Bot Lab

Initial framework to design, test, and optimize simple strategies across multiple markets
(crypto, forex, equities, indices) with strict max drawdown control.

## Objective

- Define strategy specifications in Markdown.
- Download historical data (baseline: Dukascopy).
- Run an automated loop: development -> backtest -> optimization -> retry.
- Save iterative reports for audit and comparison.

## Structure

- `cbot_farm/` modular Python package.
  - `cli.py` command-line entrypoint.
  - `pipeline.py` end-to-end cycle orchestration.
  - `ingestion.py` Dukascopy download logic.
  - `backtest.py` backtest layer (currently stub).
  - `optimization.py` parameter/gates logic.
  - `config.py` configuration loading.
- `scripts/run_cycle.py` compatibility launcher.
- `config/` instrument universe, timeframes, and risk constraints.
- `data/dukascopy/` downloaded historical data.
- `reports/` per-run JSON outputs.

## Prerequisites

- Python 3.9+
- Node.js + npm (required by `npx dukascopy-node`)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
npm run cycle
```

## npm Scripts

```bash
# Full loop
npm run cycle

# Fast single-cycle run on EURUSD 1h
npm run cycle:quick

# Ingestion only (all configured markets/symbols/timeframes)
npm run ingest

# Ingestion only for Forex 1h
npm run ingest:fx:h1

# Ingestion only for EURUSD 1h
npm run ingest:eurusd:h1

# Skip ingestion and run only the loop
npm run cycle:no-ingest

# Basic python syntax check
npm run check
```

## Direct Python Commands

```bash
python3 -m cbot_farm.cli --ingest-only --markets forex --symbols EURUSD --timeframes 1h
python3 -m cbot_farm.cli --skip-ingest --iterations 3
```

Each ingestion run writes a manifest file to `reports/ingest/manifest_*.json`.

## Dukascopy Source

Data download is executed with `dukascopy-node`, using this command shape per symbol/timeframe:

```bash
npx dukascopy-node -i <instrument> -from <YYYY-MM-DD> -to <YYYY-MM-DD> -t <timeframe> -f csv
```

For exact provider details and instrument coverage, refer to:
[https://www.dukascopy-node.app/downloading-tick-data](https://www.dukascopy-node.app/downloading-tick-data)
