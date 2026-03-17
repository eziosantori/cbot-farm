import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
import type {
  ListResponse,
  StrategyIntakeCreateResponse,
  StrategyIntakeOptionsResponse,
  StrategyIntakeSummary,
} from '../types'

function toggleValue(current: string[], value: string): string[] {
  if (current.includes(value)) {
    return current.filter((item) => item !== value)
  }
  return [...current, value]
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export default function StrategyIntakePage(): JSX.Element {
  const options = useFetch<StrategyIntakeOptionsResponse>('/strategy-intake/options')
  const [refreshToken, setRefreshToken] = useState(0)
  const history = useFetch<ListResponse<StrategyIntakeSummary>>(`/strategy-intake?limit=12&refresh=${refreshToken}`)

  const [title, setTitle] = useState('')
  const [linkedStrategyId, setLinkedStrategyId] = useState('')
  const [thesis, setThesis] = useState('')
  const [notes, setNotes] = useState('')
  const [targetMarkets, setTargetMarkets] = useState<string[]>([])
  const [targetTimeframes, setTargetTimeframes] = useState<string[]>([])
  const [targetSymbols, setTargetSymbols] = useState<string[]>([])
  const [maxDrawdownPct, setMaxDrawdownPct] = useState('12')
  const [minSharpe, setMinSharpe] = useState('1.2')
  const [maxOosDegradationPct, setMaxOosDegradationPct] = useState('30')
  const [researchPrompt, setResearchPrompt] = useState('')
  const [implementationPrompt, setImplementationPrompt] = useState('')
  const [evaluationPrompt, setEvaluationPrompt] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<StrategyIntakeCreateResponse['intake'] | null>(null)

  const marketIds = useMemo(() => Object.keys(options.data?.markets || {}), [options.data])

  const availableSymbols = useMemo(() => {
    const symbols = new Set<string>()
    for (const marketId of targetMarkets) {
      for (const symbol of options.data?.markets?.[marketId]?.symbols || []) {
        symbols.add(symbol)
      }
    }
    return Array.from(symbols).sort()
  }, [options.data, targetMarkets])

  const availableTimeframes = useMemo(() => {
    const timeframes = new Set<string>()
    for (const marketId of targetMarkets) {
      for (const timeframe of options.data?.markets?.[marketId]?.timeframes || []) {
        timeframes.add(timeframe)
      }
    }
    return Array.from(timeframes).sort()
  }, [options.data, targetMarkets])

  useEffect(() => {
    if (!options.data) {
      return
    }
    setLinkedStrategyId(options.data.defaults.linked_strategy_id || '')
    setTargetMarkets(options.data.defaults.target_markets || ['forex'])
    setTargetTimeframes(options.data.defaults.target_timeframes || ['1h'])
    setMaxDrawdownPct(String(options.data.defaults.risk_gates.max_drawdown_pct))
    setMinSharpe(String(options.data.defaults.risk_gates.min_sharpe))
    setMaxOosDegradationPct(String(options.data.defaults.risk_gates.max_oos_degradation_pct))
  }, [options.data])

  useEffect(() => {
    setTargetTimeframes((current) => current.filter((item) => availableTimeframes.includes(item)))
    setTargetSymbols((current) => current.filter((item) => availableSymbols.includes(item)))
  }, [availableSymbols, availableTimeframes])

  async function submit(): Promise<void> {
    setSaving(true)
    setError('')

    try {
      const out = await apiRequest<StrategyIntakeCreateResponse>('/strategy-intake', {
        method: 'POST',
        body: JSON.stringify({
          title,
          linked_strategy_id: linkedStrategyId,
          thesis,
          notes,
          target_markets: targetMarkets,
          target_timeframes: targetTimeframes,
          target_symbols: targetSymbols,
          risk_gates: {
            max_drawdown_pct: Number(maxDrawdownPct),
            min_sharpe: Number(minSharpe),
            max_oos_degradation_pct: Number(maxOosDegradationPct),
          },
          prompts: {
            research_prompt: researchPrompt,
            implementation_prompt: implementationPrompt,
            evaluation_prompt: evaluationPrompt,
          },
        }),
      })
      setResult(out.intake)
      setRefreshToken((value) => value + 1)
    } catch (err) {
      setError(String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main>
      <header>
        <h1>Strategy intake</h1>
        <p>
          Capture a strategy idea as a structured artifact for the LLM-driven implementation loop.{' '}
          <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section className="card">
        <div className="form-grid">
          <label>
            Idea title
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Trend breakout with session filter" />
          </label>

          <label>
            Linked bot module
            <select value={linkedStrategyId} onChange={(e) => setLinkedStrategyId(e.target.value)}>
              <option value="">New strategy idea</option>
              {Object.entries(options.data?.strategies || {}).map(([id, name]) => (
                <option key={id} value={id}>
                  {id} - {name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label>
          Thesis
          <textarea
            value={thesis}
            onChange={(e) => setThesis(e.target.value)}
            rows={5}
            style={{ width: '100%' }}
            placeholder="Describe the edge, entry logic, exit logic, and why the market inefficiency should exist."
          />
        </label>

        <div className="card" style={{ marginTop: '16px' }}>
          <h2>Targets</h2>
          <p>Select the first universe the loop should explore.</p>

          <p>
            <strong>Markets</strong>
          </p>
          <div className="kpis">
            {marketIds.map((marketId) => (
              <label className="card" key={marketId}>
                <input
                  type="checkbox"
                  checked={targetMarkets.includes(marketId)}
                  onChange={() => setTargetMarkets((current) => toggleValue(current, marketId))}
                />
                {marketId}
              </label>
            ))}
          </div>

          <p>
            <strong>Timeframes</strong>
          </p>
          <div className="kpis">
            {availableTimeframes.map((timeframe) => (
              <label className="card" key={timeframe}>
                <input
                  type="checkbox"
                  checked={targetTimeframes.includes(timeframe)}
                  onChange={() => setTargetTimeframes((current) => toggleValue(current, timeframe))}
                />
                {timeframe}
              </label>
            ))}
          </div>

          <p>
            <strong>Symbols</strong>
          </p>
          <div className="kpis">
            {availableSymbols.length === 0 ? (
              <p>No symbols available until at least one market is selected.</p>
            ) : (
              availableSymbols.map((symbol) => (
                <label className="card" key={symbol}>
                  <input
                    type="checkbox"
                    checked={targetSymbols.includes(symbol)}
                    onChange={() => setTargetSymbols((current) => toggleValue(current, symbol))}
                  />
                  {symbol}
                </label>
              ))
            )}
          </div>
        </div>

        <div className="card" style={{ marginTop: '16px' }}>
          <h2>Risk gates</h2>
          <div className="form-grid">
            <label>
              Max drawdown %
              <input type="number" step="0.1" value={maxDrawdownPct} onChange={(e) => setMaxDrawdownPct(e.target.value)} />
            </label>
            <label>
              Min Sharpe
              <input type="number" step="0.1" value={minSharpe} onChange={(e) => setMinSharpe(e.target.value)} />
            </label>
            <label>
              Max OOS degradation %
              <input
                type="number"
                step="0.1"
                value={maxOosDegradationPct}
                onChange={(e) => setMaxOosDegradationPct(e.target.value)}
              />
            </label>
          </div>
        </div>

        <label style={{ display: 'block', marginTop: '16px' }}>
          Notes for the loop
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            style={{ width: '100%' }}
            placeholder="Include market caveats, implementation hints, or constraints."
          />
        </label>

        <div className="card" style={{ marginTop: '16px' }}>
          <h2>Prompt overrides</h2>
          <p>Leave these blank to let the backend generate prompts automatically from the intake.</p>
          <label>
            Research prompt
            <textarea value={researchPrompt} onChange={(e) => setResearchPrompt(e.target.value)} rows={4} style={{ width: '100%' }} />
          </label>
          <label>
            Implementation prompt
            <textarea
              value={implementationPrompt}
              onChange={(e) => setImplementationPrompt(e.target.value)}
              rows={4}
              style={{ width: '100%' }}
            />
          </label>
          <label>
            Evaluation prompt
            <textarea
              value={evaluationPrompt}
              onChange={(e) => setEvaluationPrompt(e.target.value)}
              rows={4}
              style={{ width: '100%' }}
            />
          </label>
        </div>

        <p>
          <button onClick={() => void submit()} disabled={saving || options.loading}>
            {saving ? 'Saving...' : 'Create intake artifact'}
          </button>
        </p>

        {error ? <p className="error">{error}</p> : null}
      </section>

      {result ? (
        <section className="card">
          <h2>Latest artifact</h2>
          <p>
            <strong>Intake:</strong> {result.intake_id}
          </p>
          <p>
            <strong>Artifact path:</strong> {result.artifact_path}
          </p>
          <p>
            <strong>Status:</strong> {result.status}
          </p>
          <p>
            <strong>Generated prompts:</strong>
          </p>
          <pre>{JSON.stringify(result.prompts, null, 2)}</pre>
        </section>
      ) : null}

      <section>
        <h2>Recent intake artifacts</h2>
        {history.error ? <p className="error">{history.error}</p> : null}
        {!history.data?.items?.length ? (
          <p>No strategy intake artifacts created yet.</p>
        ) : (
          history.data.items.map((item) => (
            <div className="card" key={item.intake_id} style={{ marginBottom: '12px' }}>
              <p>
                <strong>{item.title}</strong> - {item.status}
              </p>
              <p>
                <strong>ID:</strong> {item.intake_id}
              </p>
              <p>
                <strong>Linked strategy:</strong> {item.linked_strategy_id || 'new strategy idea'}
              </p>
              <p>
                <strong>Targets:</strong> {item.target_markets.join(', ') || '-'} | {item.target_timeframes.join(', ') || '-'}
              </p>
              <p>
                <strong>Created:</strong> {formatDate(item.created_at)}
              </p>
              <p>
                <strong>Artifact:</strong> {item.artifact_path}
              </p>
            </div>
          ))
        )}
      </section>
    </main>
  )
}
