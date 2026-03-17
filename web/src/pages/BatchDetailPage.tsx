import { Link, useParams } from 'react-router-dom'

import { useFetch } from '../api'
import Badge from '../components/Badge'
import { MetricBarChart, TrendChart } from '../components/MetricsChart'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
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

function fmt(raw: unknown, suffix = ''): string {
  const value = numValue(raw)
  return value === null ? '-' : `${value.toFixed(2)}${suffix}`
}

function qualityTone(scenario: BatchScenario): 'neutral' | 'accent' | 'success' | 'warning' {
  const metrics = (scenario.best?.metrics as JsonRecord | undefined) || {}
  const ret = numValue(metrics.total_return_pct)
  const dd = numValue(metrics.max_drawdown_pct)
  const oos = numValue(metrics.oos_degradation_pct)

  if ((ret ?? -999) > 0 && (dd ?? 999) <= 4 && (oos ?? 999) <= 80) {
    return 'success'
  }
  if ((ret ?? -999) > 0) {
    return 'accent'
  }
  return 'warning'
}

function ScenarioPanel({ scenario }: { scenario: BatchScenario }): JSX.Element {
  const metrics = ((scenario.best?.metrics as JsonRecord | undefined) || {}) as JsonRecord
  const chartPoints = [
    { label: 'return %', value: numValue(metrics.total_return_pct) },
    { label: 'sharpe', value: numValue(metrics.sharpe) },
    { label: 'max DD %', value: numValue(metrics.max_drawdown_pct) },
    { label: 'oos degr %', value: numValue(metrics.oos_degradation_pct) },
  ]
    .filter((point): point is { label: string; value: number } => point.value !== null)
    .map((point) => ({ label: point.label, value: point.value }))

  const equityPoints = (scenario.best_equity_curve || []).map((point, idx) => ({
    label: String(idx + 1),
    value: point.equity,
  }))

  return (
    <section className="surface-card batch-scenario">
      <div className="surface-card__header">
        <div>
          <p className="surface-card__eyebrow">{scenario.market || '-'} / {scenario.symbol || '-'} / {scenario.timeframe || '-'}</p>
          <h2>{scenario.name}</h2>
        </div>
        <Badge
          label={scenario.promoted_count ? 'promoted candidate' : 'needs review'}
          tone={qualityTone(scenario)}
        />
      </div>

      <div className="metric-strip">
        <div>
          <span>Return</span>
          <strong>{fmt(metrics.total_return_pct, '%')}</strong>
        </div>
        <div>
          <span>Sharpe</span>
          <strong>{fmt(metrics.sharpe)}</strong>
        </div>
        <div>
          <span>Max DD</span>
          <strong>{fmt(metrics.max_drawdown_pct, '%')}</strong>
        </div>
        <div>
          <span>OOS</span>
          <strong>{fmt(metrics.oos_degradation_pct, '%')}</strong>
        </div>
      </div>

      <div className="scenario-grid">
        <div className="scenario-grid__main">
          <div className="card">
            <p>
              <strong>Reports:</strong> {String(scenario.reports ?? '-')} | <strong>Iterations:</strong>{' '}
              {String(scenario.iterations ?? '-')} | <strong>Trades:</strong> {String(scenario.best_trades_count ?? '-')}
            </p>
            <p>
              <strong>Best run:</strong>{' '}
              {scenario.best_run_id ? <Link to={`/runs/${scenario.best_run_id}`}>{scenario.best_run_id}</Link> : '-'}
            </p>
            <p>
              <strong>Candidate index:</strong> {String(scenario.best?.candidate_index ?? '-')} /{' '}
              {String(scenario.best?.total_candidates ?? '-')}
            </p>
          </div>

          {equityPoints.length >= 2 ? (
            <TrendChart title="Best run equity curve" points={equityPoints} />
          ) : (
            <div className="card">
              <p>No equity curve data available.</p>
            </div>
          )}
        </div>

        <div className="scenario-grid__side">
          {chartPoints.length > 0 ? <MetricBarChart title="Best run ratios" points={chartPoints} /> : null}
          <div className="card">
            <h3>Parameter set</h3>
            <pre>{JSON.stringify(scenario.best?.params || {}, null, 2)}</pre>
          </div>
        </div>
      </div>
    </section>
  )
}

export default function BatchDetailPage(): JSX.Element {
  const { batchId = '' } = useParams()
  const detail = useFetch<BatchDetailResponse>(`/batches/${batchId}`)

  if (detail.loading) {
    return (
      <main className="page">
        <p>Loading batch detail...</p>
      </main>
    )
  }

  if (detail.error) {
    return (
      <main className="page">
        <p className="error">{detail.error}</p>
        <p>
          <Link to="/batches">Back to batches</Link>
        </p>
      </main>
    )
  }

  const summary = (detail.data?.summary || {}) as JsonRecord
  const scenarios = detail.data?.scenarios || []
  const bestReturn = scenarios.reduce<number | null>((best, scenario) => {
    const current = numValue((scenario.best?.metrics as JsonRecord | undefined)?.total_return_pct)
    if (current === null) {
      return best
    }
    if (best === null || current > best) {
      return current
    }
    return best
  }, null)

  return (
    <main className="page">
      <PageHeader
        eyebrow="Observe"
        title={`Batch ${batchId}`}
        description={<p>Inspect scenario quality, best-run behavior, and parameter choices for this optimization batch.</p>}
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/batches">
              Back to batches
            </Link>
          </div>
        }
      />

      <section className="stat-grid">
        <StatCard label="Strategy" value={String(summary.strategy || '-')} detail="Canonical strategy under evaluation." />
        <StatCard label="Created at" value={String(summary.created_at || '-')} detail="Batch artifact timestamp." />
        <StatCard label="Scenarios" value={String(scenarios.length)} detail="Distinct market / symbol / timeframe cases." />
        <StatCard label="Best return" value={bestReturn === null ? '-' : `${bestReturn.toFixed(2)}%`} tone="accent" detail="Highest return found in this batch." />
      </section>

      {scenarios.map((scenario) => (
        <ScenarioPanel key={scenario.name} scenario={scenario} />
      ))}
    </main>
  )
}
