# Multi-Market Bot Lab

Initial framework to design, test, and optimize simple strategies across multiple markets
(crypto, forex, equities, indices) with strict max drawdown control.

## Objective

- Define strategy specifications in Markdown.
- Download historical data (baseline: Dukascopy).
- Run an automated loop: development -> backtest -> optimization -> retry.
- Save iterative reports for audit and comparison.

## Structure

- `bots/` strategy files (human-readable, one bot per file).
  - `base.py` strategy base class.
  - `ema_cross_atr.py` first concrete bot.
- `cbot_farm/` engine and orchestration package.
  - `cli.py` command-line entrypoint.
  - `pipeline.py` end-to-end cycle orchestration.
  - `backtest.py` execution engine (strategy-agnostic).
  - `ingestion.py` Dukascopy download logic.
  - `optimization.py` risk gates.
  - `indicators.py` shared indicators.
  - `config.py` configuration loading.
- `scripts/run_cycle.py` compatibility launcher.
- `scripts/verify_instruments.py` instrument validation utility.
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

# List available strategy ids
npm run list:strategies

# Ingestion only (all configured markets/symbols/timeframes)
npm run ingest

# Ingestion only for Forex 1h
npm run ingest:fx:h1

# Ingestion only for EURUSD 1h
npm run ingest:eurusd:h1

# Ingestion only for NAS100 1h
npm run ingest:nas:h1

# Skip ingestion and run only the loop
npm run cycle:no-ingest

# Basic python syntax check
npm run check

# Validate all configured symbols against Dukascopy
npm run verify:instruments
```

## Direct Python Commands

```bash
python3 -m cbot_farm.cli --list-strategies
python3 -m cbot_farm.cli --strategy ema_cross_atr --ingest-only --markets forex --symbols EURUSD --timeframes 1h
python3 -m cbot_farm.cli --strategy ema_cross_atr --skip-ingest --iterations 3
python3 scripts/verify_instruments.py
```

Each ingestion run writes a manifest file to `reports/ingest/manifest_*.json`.

## Optimization Parameter Space

The cycle supports configurable parameter ranges per strategy (panel-ready model):

- `enabled` (true/false)
- `type` (`int` or `float`)
- if enabled: `min`, `max`, `step`
- if disabled: fixed `value`

Current configuration lives in:

- `/Users/esantori/Documents/cbot-farm/config/risk.json`
  - `optimization.parameter_space.ema_cross_atr`

Runtime behavior:

- when parameter space is configured, iterations use generated candidates (grid/random mode);
- when missing, fallback is strategy native sampling (`sample_params`).

Each run report now includes:

- `optimization.mode` (source, candidate index, counts, truncation)
- `optimization.space` (effective parameter-space metadata)


## Dukascopy Source

Data download is executed with `dukascopy-node`, using this command shape per symbol/timeframe:

```bash
npx dukascopy-node -i <instrument> -from <YYYY-MM-DD> -to <YYYY-MM-DD> -t <timeframe> -f csv
```

## Instrument Discovery / Validation Commands

Debug command used to inspect provider-side instrument validation details:

```bash
npx dukascopy-node -d -i __invalid__ -from 2024-01-01 -to 2024-01-02 -t h1 -f csv
```

Authoritative check used in this project (runs a real short download check for each configured symbol after mapping):

```bash
npm run verify:instruments
```

For exact provider details and instrument coverage, refer to:
[https://www.dukascopy-node.app/downloading-tick-data](https://www.dukascopy-node.app/downloading-tick-data)
