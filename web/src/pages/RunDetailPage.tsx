import { Link, useParams } from 'react-router-dom'

import { useFetch } from '../api'
import { MetricBarChart } from '../components/MetricsChart'
import type { JsonRecord, RunDetailResponse } from '../types'

function MetricGrid({ metrics }: { metrics: JsonRecord }): JSX.Element {
  const entries = Object.entries(metrics || {})
  if (!entries.length) {
    return <p>No metrics available.</p>
  }

  return (
    <div className="kpis">
      {entries.map(([key, value]) => (
        <div className="card" key={key}>
          <h3>{key}</h3>
          <p>{String(value)}</p>
        </div>
      ))}
    </div>
  )
}

function numericValue(raw: unknown): number | null {
  if (typeof raw === 'number') {
    return raw
  }
  if (typeof raw === 'string') {
    const parsed = Number(raw)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

export default function RunDetailPage(): JSX.Element {
  const { runId = '' } = useParams()
  const run = useFetch<RunDetailResponse>(`/runs/${runId}`)

  if (run.loading) {
    return (
      <main>
        <p>Loading run detail...</p>
      </main>
    )
  }

  if (run.error) {
    return (
      <main>
        <p className="error">{run.error}</p>
        <p>
          <Link to="/">Back to dashboard</Link>
        </p>
      </main>
    )
  }

  const payload = (run.data?.payload || {}) as JsonRecord
  const backtest = (payload.backtest as JsonRecord | undefined) || {}
  const target = (payload.target as JsonRecord | undefined) || {}
  const timeframes = (payload.timeframes as unknown[] | undefined) || []
  const metrics =
    ((payload.metrics as JsonRecord | undefined) ||
      (backtest.metrics as JsonRecord | undefined) ||
      {}) as JsonRecord

  const chartPoints = [
    { label: 'return %', value: numericValue(metrics.total_return_pct) },
    { label: 'sharpe', value: numericValue(metrics.sharpe) },
    { label: 'max DD %', value: numericValue(metrics.max_drawdown_pct) },
    { label: 'oos degr %', value: numericValue(metrics.oos_degradation_pct) },
  ]
    .filter((p): p is { label: string; value: number } => p.value !== null)
    .map((p) => ({ label: p.label, value: p.value }))

  return (
    <main>
      <header>
        <h1>Run detail: {run.data?.run_id}</h1>
        <p>
          <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section>
        <h2>Key metrics</h2>
        <MetricGrid metrics={metrics} />
      </section>

      <section>
        <h2>Charts</h2>
        {chartPoints.length ? (
          <MetricBarChart title="Run metric distribution" points={chartPoints} />
        ) : (
          <p>No chartable metrics found.</p>
        )}
      </section>

      <section>
        <h2>Metadata</h2>
        <div className="card">
          <p>
            <strong>Strategy:</strong> {String(payload.strategy_id || payload.strategy || '-')}
          </p>
          <p>
            <strong>Market:</strong> {String(payload.market || target.market || '-')}
          </p>
          <p>
            <strong>Symbol:</strong> {String(payload.symbol || target.symbol || '-')}
          </p>
          <p>
            <strong>Timeframe:</strong>{' '}
            {String(target.timeframe || (timeframes.length ? timeframes[0] : '-'))}
          </p>
          <p>
            <strong>Status:</strong> {String(payload.status || backtest.status || '-')}
          </p>
        </div>
      </section>

      <section>
        <h2>Raw payload</h2>
        <pre>{JSON.stringify(payload, null, 2)}</pre>
      </section>
    </main>
  )
}
