import { Link } from 'react-router-dom'

import { useFetch } from '../api'
import StatCard from '../components/StatCard'
import { TrendChart } from '../components/MetricsChart'
import PageHeader from '../components/PageHeader'
import Table from '../components/Table'
import type {
  BatchItem,
  HealthResponse,
  IndexStatusResponse,
  JsonRecord,
  ListResponse,
  ManifestItem,
  RunItem,
  WorkflowBoardResponse,
} from '../types'

function numMetric(metrics: JsonRecord | undefined, key: string): number | null {
  const raw = metrics?.[key]
  if (typeof raw === 'number') {
    return raw
  }
  if (typeof raw === 'string') {
    const parsed = Number(raw)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function formatMetric(value: number | null | undefined, suffix = ''): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '-'
  }
  return `${value.toFixed(2)}${suffix}`
}

export default function DashboardPage(): JSX.Element {
  const health = useFetch<HealthResponse>('/health')
  const indexStatus = useFetch<IndexStatusResponse>('/index/status')
  const runs = useFetch<ListResponse<RunItem>>('/runs?limit=6')
  const manifests = useFetch<ListResponse<ManifestItem>>('/ingest-manifests?limit=6')
  const workflow = useFetch<WorkflowBoardResponse>('/strategy-workflow')
  const batches = useFetch<ListResponse<BatchItem>>('/batches?limit=4')

  const trendPoints = (runs.data?.items || [])
    .map((row, idx) => {
      const ret = numMetric(row.metrics, 'total_return_pct')
      if (ret === null) {
        return null
      }
      return {
        label: row.run_id || `run-${idx + 1}`,
        value: ret,
      }
    })
    .filter((item): item is { label: string; value: number } => item !== null)
    .reverse()

  const activeWorkflowItems = workflow.data?.items.filter((item) => item.state !== 'archived').length ?? 0
  const candidateCount = workflow.data?.counts?.candidate ?? 0
  const approvedCount = workflow.data?.counts?.approved ?? 0
  const latestBatch = batches.data?.items?.[0]

  return (
    <main className="page">
      <PageHeader
        eyebrow="Observe"
        title="Research lab dashboard"
        description={
          <p>
            Monitor the state of the strategy farm, inspect fresh activity, and jump into the next operational action
            without opening raw JSON files.
          </p>
        }
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/intake">
              Create intake
            </Link>
            <Link className="quick-actions__link" to="/simulations">
              Launch simulation
            </Link>
            <Link className="quick-actions__link" to="/batches">
              Review batches
            </Link>
          </div>
        }
      />

      <section className="hero-panel">
        <div className="hero-panel__content">
          <p className="hero-panel__eyebrow">Lab state</p>
          <h2 className="hero-panel__title">The platform is now structured around Observe, Build, Simulate, and Govern.</h2>
          <p className="hero-panel__copy">
            Use intake artifacts to formalize ideas, simulations to validate single scenarios, and batch analytics plus
            workflow to decide whether a strategy deserves more capital or more criticism.
          </p>
        </div>
        <div className="hero-panel__signal">
          <p className="hero-panel__signal-label">Latest batch</p>
          <p className="hero-panel__signal-value">{latestBatch?.batch_id || 'No batch yet'}</p>
          <p className="hero-panel__signal-copy">
            Best return {formatMetric(latestBatch?.best_return_pct, '%')} across {latestBatch?.scenarios ?? 0} scenarios
          </p>
        </div>
      </section>

      <section className="stat-grid">
        <StatCard
          label="API health"
          value={health.loading ? 'Loading' : health.data?.status || 'Error'}
          tone={health.data?.status === 'ok' ? 'accent' : 'warning'}
          detail={health.error || 'FastAPI service reachable'}
        />
        <StatCard
          label="Indexed reports"
          value={indexStatus.loading ? '...' : String(indexStatus.data?.runs_count ?? runs.data?.total ?? '-')}
          detail={
            indexStatus.data?.stale ? 'SQLite index is stale, API is falling back to filesystem reads.' : 'Index ready for query paths.'
          }
        />
        <StatCard
          label="Active strategies"
          value={String(activeWorkflowItems)}
          detail={`${candidateCount} candidate | ${approvedCount} approved`}
        />
        <StatCard
          label="Latest manifests"
          value={String(manifests.data?.total ?? '-')}
          detail={manifests.data?.items?.[0]?.manifest_id || 'No ingest manifest yet'}
        />
      </section>

      <section className="dashboard-grid">
        <section className="surface-card surface-card--tall">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Performance signal</p>
              <h2>Latest return trend</h2>
            </div>
            <Link to="/batches">Open batch analytics</Link>
          </div>
          {trendPoints.length >= 2 ? (
            <TrendChart title="Total return % across latest runs" points={trendPoints} />
          ) : (
            <p>No trend data available yet.</p>
          )}
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Immediate actions</p>
              <h2>Next operator moves</h2>
            </div>
          </div>
          <div className="action-stack">
            <Link className="action-card" to="/intake">
              <span className="action-card__tag">Build</span>
              <strong>Capture a new strategy idea</strong>
              <span>Turn a thesis into a structured prompt bundle for the loop.</span>
            </Link>
            <Link className="action-card" to="/simulations">
              <span className="action-card__tag">Simulate</span>
              <strong>Launch a manual scenario</strong>
              <span>Test a strategy with direct parameter overrides before a larger batch.</span>
            </Link>
            <Link className="action-card" to="/workflow">
              <span className="action-card__tag">Govern</span>
              <strong>Review lifecycle state</strong>
              <span>Move strategies across research, backtest, candidate, and paper states.</span>
            </Link>
          </div>
        </section>
      </section>

      <section className="dashboard-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Latest runs</p>
              <h2>Backtest activity</h2>
            </div>
          </div>
          {runs.error ? <p className="error">{runs.error}</p> : null}
          <Table<RunItem>
            columns={[
              {
                key: 'run_id',
                label: 'Run ID',
                render: (row) => <Link to={`/runs/${row.run_id}`}>{row.run_id}</Link>,
              },
              { key: 'strategy_id', label: 'Strategy' },
              { key: 'market', label: 'Market' },
              { key: 'symbol', label: 'Symbol' },
              { key: 'timeframe', label: 'TF' },
              {
                key: 'metrics',
                label: 'Return %',
                render: (row) => formatMetric(numMetric(row.metrics, 'total_return_pct')),
              },
            ]}
            rows={runs.data?.items || []}
          />
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Ingestion</p>
              <h2>Latest manifests</h2>
            </div>
          </div>
          {manifests.error ? <p className="error">{manifests.error}</p> : null}
          <Table<ManifestItem>
            columns={[
              {
                key: 'manifest_id',
                label: 'Manifest ID',
                render: (row) => <Link to={`/ingestion/${row.manifest_id}`}>{row.manifest_id}</Link>,
              },
              { key: 'created_at', label: 'Date' },
              { key: 'status', label: 'Status' },
              { key: 'rows', label: 'Rows' },
              { key: 'ok', label: 'OK' },
              { key: 'failed', label: 'Failed' },
            ]}
            rows={manifests.data?.items || []}
          />
        </section>
      </section>
    </main>
  )
}
