import { Link, useParams } from 'react-router-dom'

import { useFetch } from '../api'
import { MetricBarChart, TrendChart } from '../components/MetricsChart'
import type { BatchDetailResponse, BatchScenario, JsonRecord } from '../types'

function numValue(raw: unknown): number | null {
  if (typeof raw === 'number') {
    return raw
  }
  if (typeof raw === 'string') {
    const parsed = Number(raw)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function ScenarioPanel({ scenario }: { scenario: BatchScenario }): JSX.Element {
  const best = (scenario.best || {}) as JsonRecord
  const metrics = (best.metrics as JsonRecord | undefined) || {}
  const chartPoints = [
    { label: 'return %', value: numValue(metrics.total_return_pct) },
    { label: 'sharpe', value: numValue(metrics.sharpe) },
    { label: 'max DD %', value: numValue(metrics.max_drawdown_pct) },
    { label: 'oos degr %', value: numValue(metrics.oos_degradation_pct) }
  ]
    .filter((p): p is { label: string; value: number } => p.value !== null)
    .map((p) => ({ label: p.label, value: p.value }))

  const equityPoints = (scenario.best_equity_curve || []).map((p, idx) => ({
    label: String(idx + 1),
    value: p.equity
  }))

  return (
    <section>
      <h3>{scenario.name}</h3>
      <div className="card">
        <p>
          <strong>Market/Symbol/TF:</strong> {String(scenario.market || '-')} / {String(scenario.symbol || '-')} /{' '}
          {String(scenario.timeframe || '-')}
        </p>
        <p>
          <strong>Reports:</strong> {String(scenario.reports ?? '-')} | <strong>Promoted:</strong>{' '}
          {String(scenario.promoted_count ?? '-')}
        </p>
        <p>
          <strong>Best run:</strong>{' '}
          {scenario.best_run_id ? <Link to={`/runs/${scenario.best_run_id}`}>{scenario.best_run_id}</Link> : '-'}
        </p>
      </div>

      {chartPoints.length > 0 ? <MetricBarChart title="Best run ratios" points={chartPoints} /> : null}

      {equityPoints.length >= 2 ? <TrendChart title="Best run equity curve" points={equityPoints} /> : <p>No equity curve data available.</p>}
    </section>
  )
}

export default function BatchDetailPage(): JSX.Element {
  const { batchId = '' } = useParams()
  const detail = useFetch<BatchDetailResponse>(`/batches/${batchId}`)

  if (detail.loading) {
    return (
      <main>
        <p>Loading batch detail...</p>
      </main>
    )
  }

  if (detail.error) {
    return (
      <main>
        <p className="error">{detail.error}</p>
        <p>
          <Link to="/batches">Back to batches</Link>
        </p>
      </main>
    )
  }

  const summary = (detail.data?.summary || {}) as JsonRecord
  const scenarios = detail.data?.scenarios || []

  return (
    <main>
      <header>
        <h1>Batch detail: {batchId}</h1>
        <p>
          <Link to="/batches">Back to batches</Link>
        </p>
      </header>

      <section className="kpis">
        <div className="card">
          <h3>Strategy</h3>
          <p>{String(summary.strategy || '-')}</p>
        </div>
        <div className="card">
          <h3>Created At</h3>
          <p>{String(summary.created_at || '-')}</p>
        </div>
        <div className="card">
          <h3>Max retries</h3>
          <p>{String(summary.max_retries || '-')}</p>
        </div>
        <div className="card">
          <h3>Scenarios</h3>
          <p>{String(scenarios.length)}</p>
        </div>
      </section>

      {scenarios.map((scenario) => (
        <ScenarioPanel key={scenario.name} scenario={scenario} />
      ))}
    </main>
  )
}
