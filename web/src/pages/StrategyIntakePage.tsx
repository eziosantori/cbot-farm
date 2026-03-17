import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
import Badge from '../components/Badge'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
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

function ChoiceChip({
  label,
  active,
  onToggle,
}: {
  label: string
  active: boolean
  onToggle: () => void
}): JSX.Element {
  return (
    <label className={active ? 'choice-chip choice-chip--active' : 'choice-chip'}>
      <input type="checkbox" checked={active} onChange={onToggle} />
      <span>{label}</span>
    </label>
  )
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
    <main className="page">
      <PageHeader
        eyebrow="Build"
        title="Strategy intake"
        description={<p>Capture a strategy thesis as a structured artifact the LLM loop can implement, test, and critique with clear constraints.</p>}
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/workflow">
              Open workflow
            </Link>
            <button onClick={() => void submit()} disabled={saving || options.loading}>
              {saving ? 'Saving...' : 'Create intake artifact'}
            </button>
          </div>
        }
      />

      <section className="stat-grid">
        <StatCard label="Linked bot" value={linkedStrategyId || 'new idea'} tone="accent" detail="Attach to an existing bot or create a fresh thesis." />
        <StatCard label="Markets" value={String(targetMarkets.length)} detail={targetMarkets.join(', ') || 'Select at least one market.'} />
        <StatCard label="Timeframes" value={String(targetTimeframes.length)} detail={targetTimeframes.join(', ') || 'Select at least one timeframe.'} />
        <StatCard label="Recent artifacts" value={String(history.data?.total ?? 0)} detail="Saved strategy briefs available for later implementation." />
      </section>

      <section className="panel-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Strategy brief</p>
              <h2>Core thesis</h2>
            </div>
            <Badge label={result ? result.status : 'draft'} tone={result ? 'success' : 'neutral'} />
          </div>

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
              rows={6}
              placeholder="Describe the edge, entry logic, exit logic, and why the market inefficiency should exist."
            />
          </label>

          <label>
            Notes for the loop
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              placeholder="Include market caveats, implementation hints, or constraints."
            />
          </label>

          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Artifact preview</p>
              <h2>Latest generated bundle</h2>
            </div>
          </div>

          {result ? (
            <div className="section-stack">
              <div className="result-grid">
                <div>
                  <span>Intake id</span>
                  <strong className="mono-text">{result.intake_id}</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong>{result.status}</strong>
                </div>
              </div>
              <div className="card">
                <p>
                  <strong>Artifact path:</strong> <span className="mono-text">{result.artifact_path}</span>
                </p>
                <pre>{JSON.stringify(result.prompts, null, 2)}</pre>
              </div>
            </div>
          ) : (
            <p className="subtle-text">Create an intake artifact to preview the generated prompt bundle and saved metadata.</p>
          )}
        </section>
      </section>

      <section className="surface-card">
        <div className="surface-card__header">
          <div>
            <p className="surface-card__eyebrow">Targets</p>
            <h2>Initial research universe</h2>
          </div>
        </div>

        <div className="section-stack">
          <div>
            <p><strong>Markets</strong></p>
            <div className="choice-grid">
              {marketIds.map((marketId) => (
                <ChoiceChip
                  key={marketId}
                  label={marketId}
                  active={targetMarkets.includes(marketId)}
                  onToggle={() => setTargetMarkets((current) => toggleValue(current, marketId))}
                />
              ))}
            </div>
          </div>

          <div>
            <p><strong>Timeframes</strong></p>
            <div className="choice-grid">
              {availableTimeframes.map((timeframe) => (
                <ChoiceChip
                  key={timeframe}
                  label={timeframe}
                  active={targetTimeframes.includes(timeframe)}
                  onToggle={() => setTargetTimeframes((current) => toggleValue(current, timeframe))}
                />
              ))}
            </div>
          </div>

          <div>
            <p><strong>Symbols</strong></p>
            <div className="choice-grid">
              {availableSymbols.length === 0 ? (
                <p className="subtle-text">No symbols available until at least one market is selected.</p>
              ) : (
                availableSymbols.map((symbol) => (
                  <ChoiceChip
                    key={symbol}
                    label={symbol}
                    active={targetSymbols.includes(symbol)}
                    onToggle={() => setTargetSymbols((current) => toggleValue(current, symbol))}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="panel-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Risk constraints</p>
              <h2>Acceptance gates</h2>
            </div>
          </div>
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
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Prompt overrides</p>
              <h2>LLM instruction bundle</h2>
            </div>
          </div>
          <div className="section-stack">
            <label>
              Research prompt
              <textarea value={researchPrompt} onChange={(e) => setResearchPrompt(e.target.value)} rows={4} />
            </label>
            <label>
              Implementation prompt
              <textarea value={implementationPrompt} onChange={(e) => setImplementationPrompt(e.target.value)} rows={4} />
            </label>
            <label>
              Evaluation prompt
              <textarea value={evaluationPrompt} onChange={(e) => setEvaluationPrompt(e.target.value)} rows={4} />
            </label>
          </div>
        </section>
      </section>

      <section className="surface-card">
        <div className="surface-card__header">
          <div>
            <p className="surface-card__eyebrow">History</p>
            <h2>Recent intake artifacts</h2>
          </div>
          <Badge label={history.loading ? 'loading' : `${history.data?.items?.length || 0} visible`} tone="neutral" />
        </div>
        {history.error ? <p className="error">{history.error}</p> : null}
        {!history.data?.items?.length ? (
          <p className="subtle-text">No strategy intake artifacts created yet.</p>
        ) : (
          <div className="history-list">
            {history.data.items.map((item) => (
              <div className="card history-card" key={item.intake_id}>
                <p>
                  <strong>{item.title}</strong> <Badge label={item.status} tone="accent" />
                </p>
                <p><strong>ID:</strong> <span className="mono-text">{item.intake_id}</span></p>
                <p><strong>Linked strategy:</strong> {item.linked_strategy_id || 'new strategy idea'}</p>
                <p><strong>Targets:</strong> {item.target_markets.join(', ') || '-'} | {item.target_timeframes.join(', ') || '-'}</p>
                <p><strong>Created:</strong> {formatDate(item.created_at)}</p>
                <p><strong>Artifact:</strong> <span className="mono-text">{item.artifact_path}</span></p>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}
