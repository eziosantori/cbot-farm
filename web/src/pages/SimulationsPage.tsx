import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
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
  }, [options.data])

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
          params
        })
      })
      setResult(out.simulation)
    } catch (err) {
      setError(String(err))
    } finally {
      setRunning(false)
    }
  }

  return (
    <main>
      <header>
        <h1>Simulation launcher</h1>
        <p>
          Launch ad-hoc backtest simulations with parameter overrides. <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section className="card">
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
          <textarea
            value={paramsText}
            onChange={(e) => setParamsText(e.target.value)}
            rows={8}
            style={{ width: '100%', fontFamily: 'monospace' }}
          />
        </label>

        <p>
          <button onClick={() => void launch()} disabled={running || options.loading}>
            {running ? 'Running...' : 'Launch simulation'}
          </button>
        </p>

        {error ? <p className="error">{error}</p> : null}
      </section>

      {result ? (
        <section className="card">
          <h2>Result</h2>
          <p>
            <strong>Status:</strong> {result.status}
          </p>
          <p>
            <strong>Run:</strong> <Link to={`/runs/${result.run_id}`}>{result.run_id}</Link>
          </p>
          <p>
            <strong>Report path:</strong> {result.report_path}
          </p>
          <pre>{JSON.stringify(result.metrics, null, 2)}</pre>
        </section>
      ) : null}
    </main>
  )
}
