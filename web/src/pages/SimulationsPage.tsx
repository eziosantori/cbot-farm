import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
import Badge from '../components/Badge'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import type { JsonRecord, SimOptionsResponse, SimRunResponse } from '../types'

function parseParams(raw: string): JsonRecord {
  if (!raw.trim()) {
    return {}
  }
  const parsed = JSON.parse(raw)
  if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
    return parsed as JsonRecord
  }
  throw new Error('params must be a JSON object')
}

function metricValue(raw: unknown, suffix = ''): string {
  if (typeof raw === 'number') {
    return `${raw.toFixed(2)}${suffix}`
  }
  if (typeof raw === 'string') {
    const parsed = Number(raw)
    if (Number.isFinite(parsed)) {
      return `${parsed.toFixed(2)}${suffix}`
    }
  }
  return '-'
}

export default function SimulationsPage(): JSX.Element {
  const options = useFetch<SimOptionsResponse>('/simulations/options')

  const [strategyId, setStrategyId] = useState('ema_cross_atr')
  const [market, setMarket] = useState('forex')
  const [symbol, setSymbol] = useState('EURUSD')
  const [timeframe, setTimeframe] = useState('1h')
  const [paramsText, setParamsText] = useState('{\n  "rsi_gate": 55,\n  "atr_vol_ratio_max": 1.8\n}')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<SimRunResponse['simulation'] | null>(null)

  const marketCfg = useMemo(() => options.data?.markets?.[market], [options.data, market])

  useEffect(() => {
    if (!options.data) {
      return
    }
    const defaultStrategy = options.data.defaults?.strategy_id || 'ema_cross_atr'
    setStrategyId(defaultStrategy)

    const marketIds = Object.keys(options.data.markets || {})
    if (marketIds.length > 0 && !marketIds.includes(market)) {
      setMarket(marketIds[0])
    }
  }, [options.data, market])

  useEffect(() => {
    if (!marketCfg) {
      return
    }
    if (!marketCfg.symbols.includes(symbol)) {
      setSymbol(marketCfg.symbols[0] || '')
    }
    if (!marketCfg.timeframes.includes(timeframe)) {
      setTimeframe(marketCfg.timeframes[0] || '')
    }
  }, [marketCfg, symbol, timeframe])

  async function launch(): Promise<void> {
    setError('')
    setRunning(true)
    setResult(null)

    try {
      const params = parseParams(paramsText)
      const out = await apiRequest<SimRunResponse>('/simulations/run', {
        method: 'POST',
        body: JSON.stringify({
          strategy_id: strategyId,
          market,
          symbol,
          timeframe,
          params,
        }),
      })
      setResult(out.simulation)
    } catch (err) {
      setError(String(err))
    } finally {
      setRunning(false)
    }
  }

  return (
    <main className="page">
      <PageHeader
        eyebrow="Simulate"
        title="Simulation launcher"
        description={<p>Run targeted what-if scenarios with direct parameter overrides before committing to a larger batch or campaign.</p>}
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/optimization">
              Open optimization
            </Link>
            <button onClick={() => void launch()} disabled={running || options.loading}>
              {running ? 'Running...' : 'Launch simulation'}
            </button>
          </div>
        }
      />

      <section className="stat-grid">
        <StatCard label="Strategy" value={strategyId} tone="accent" detail="Current canonical bot under simulation." />
        <StatCard label="Market / Symbol" value={`${market} / ${symbol}`} detail="Execution target selected for the manual run." />
        <StatCard label="Timeframe" value={timeframe} detail="Single timeframe executed in this ad-hoc test." />
        <StatCard label="Last result" value={result?.status || '-'} detail={result ? result.run_id : 'No simulation launched in this session.'} />
      </section>

      <section className="panel-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Scenario builder</p>
              <h2>Simulation inputs</h2>
            </div>
            <Badge label={options.loading ? 'loading' : 'ready'} tone={options.loading ? 'neutral' : 'accent'} />
          </div>

          <div className="form-grid">
            <label>
              Strategy
              <select value={strategyId} onChange={(e) => setStrategyId(e.target.value)}>
                {Object.entries(options.data?.strategies || {}).map(([id, name]) => (
                  <option key={id} value={id}>
                    {id} - {name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Market
              <select value={market} onChange={(e) => setMarket(e.target.value)}>
                {Object.keys(options.data?.markets || {}).map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Symbol
              <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
                {(marketCfg?.symbols || []).map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Timeframe
              <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
                {(marketCfg?.timeframes || []).map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label>
            Params override (JSON)
            <textarea value={paramsText} onChange={(e) => setParamsText(e.target.value)} rows={12} className="mono-text" />
          </label>

          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Execution summary</p>
              <h2>Run output</h2>
            </div>
          </div>

          {result ? (
            <div className="section-stack">
              <div className="result-grid">
                <div>
                  <span>Status</span>
                  <strong>{result.status}</strong>
                </div>
                <div>
                  <span>Return</span>
                  <strong>{metricValue(result.metrics.total_return_pct, '%')}</strong>
                </div>
                <div>
                  <span>Sharpe</span>
                  <strong>{metricValue(result.metrics.sharpe)}</strong>
                </div>
                <div>
                  <span>Max DD</span>
                  <strong>{metricValue(result.metrics.max_drawdown_pct, '%')}</strong>
                </div>
              </div>

              <div className="card">
                <p>
                  <strong>Run:</strong> <Link to={`/runs/${result.run_id}`}>{result.run_id}</Link>
                </p>
                <p>
                  <strong>Report path:</strong> <span className="mono-text">{result.report_path}</span>
                </p>
                <p>
                  <strong>Gates:</strong>
                </p>
                <pre>{JSON.stringify(result.gates, null, 2)}</pre>
              </div>
            </div>
          ) : (
            <p className="subtle-text">Launch a simulation to see metrics, run id, and gate evaluation here.</p>
          )}
        </section>
      </section>
    </main>
  )
}
