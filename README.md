# Multi-Market Bot Lab

Framework to design, test, and optimize strategies across crypto, forex, equities, indices, and commodities with controlled drawdown.

## Tech Stack
- Python engine (`cbot_farm/`, `bots/`)
- FastAPI backend (`api/`)
- React + Vite + TypeScript frontend (`web/`)
- SQLite report index (SQLAlchemy ORM)
- Package manager: `pnpm`
- Toolchain manager: `Volta`

## First Setup (Volta + pnpm)

### 1) Install Volta
macOS / Linux:
```bash
curl https://get.volta.sh | bash
```

After installation, restart your shell and verify:
```bash
volta --version
```

### 2) Install pinned toolchain
From repo root (`/Users/esantori/Documents/cbot-farm`):
```bash
volta install node@22.22.0 pnpm@10.6.2
```

Tool versions are pinned in:
- `/Users/esantori/Documents/cbot-farm/package.json`
- `/Users/esantori/Documents/cbot-farm/web/package.json`

### 3) Install workspace dependencies
```bash
pnpm install
```

### 4) Install Python API dependencies
```bash
pnpm run api:install
```

## First Run

```bash
# terminal 1
pnpm run api:dev

# terminal 2
pnpm run web:dev
```

Optional (rebuild SQLite index with API running):
```bash
pnpm run index:rebuild
```

## Main Scripts (root)

```bash
pnpm run cycle
pnpm run cycle:quick
pnpm run cycle:no-ingest
pnpm run ingest
pnpm run ingest:fx:h1
pnpm run ingest:eurusd:h1
pnpm run ingest:nas:h1
pnpm run list:strategies
pnpm run verify:instruments
pnpm run parity:backtrader

pnpm run api:dev
pnpm run web:dev
pnpm run web:typecheck
pnpm run web:build

pnpm run test:unit
pnpm run check:all
```

## API Endpoints (current)
- `GET /health`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /ingest-manifests`
- `GET /ingest-manifests/{manifest_id}`
- `GET /optimization/spaces`
- `GET /optimization/spaces/{strategy_id}`
- `PUT /optimization/spaces/{strategy_id}`
- `POST /optimization/preview/{strategy_id}`
- `GET /index/status`
- `POST /index/rebuild`
- `POST /campaigns`
- `GET /campaigns`
- `GET /campaigns/{campaign_id}`
- `POST /campaigns/{campaign_id}/pause`
- `POST /campaigns/{campaign_id}/resume`
- `POST /campaigns/{campaign_id}/cancel`
- `GET /campaigns/{campaign_id}/iterations`
- `POST /campaigns/{campaign_id}/iterations`
- `GET /campaigns/{campaign_id}/artifacts`
- `POST /export/{campaign_id}/{target}`

## Web Routes
- `/`
- `/runs/:runId`
- `/ingestion/:manifestId`
- `/optimization`

## Docs
- `/Users/esantori/Documents/cbot-farm/docs/progress-tracker.md`
- `/Users/esantori/Documents/cbot-farm/docs/strategy-development-playbook.md`
- `/Users/esantori/Documents/cbot-farm/docs/autonomous-strategy-lab-v1.md`
- `/Users/esantori/Documents/cbot-farm/docs/system-flows.md`
