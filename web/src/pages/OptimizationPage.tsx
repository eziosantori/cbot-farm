import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
import Badge from '../components/Badge'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import type {
  OptimizationParam,
  OptimizationSpace,
  OptimizationSpaceDetail,
  OptimizationSpaceList,
  OptimizationSpacePreview,
} from '../types'

function toNumber(v: string): number {
  const parsed = Number(v)
  return Number.isFinite(parsed) ? parsed : 0
}

function countEnabled(space: OptimizationSpace | null): number {
  if (!space) {
    return 0
  }
  return Object.values(space.parameters).filter((param) => param.enabled).length
}

function ParameterCard({
  name,
  param,
  updateParam,
}: {
  name: string
  param: OptimizationParam
  updateParam: (updater: (prev: OptimizationParam) => OptimizationParam) => void
}): JSX.Element {
  return (
    <article className="parameter-card">
      <div className="parameter-card__header">
        <div>
          <p className="parameter-card__name">{name}</p>
          <p className="parameter-card__type">{param.type} parameter</p>
        </div>
        <Badge label={param.enabled ? 'search' : 'fixed'} tone={param.enabled ? 'accent' : 'neutral'} />
      </div>

      <div className="parameter-card__row">
        <label>
          <input
            type="checkbox"
            checked={param.enabled}
            onChange={(e) => updateParam((prev) => ({ ...prev, enabled: e.target.checked }))}
          />
          Include in optimization
        </label>
        <select
          value={param.type}
          onChange={(e) => updateParam((prev) => ({ ...prev, type: e.target.value as 'int' | 'float' }))}
        >
          <option value="int">int</option>
          <option value="float">float</option>
        </select>
      </div>

      {param.enabled ? (
        <div className="parameter-card__grid">
          <label>
            Min
            <input
              type="number"
              step="any"
              value={param.min ?? ''}
              onChange={(e) => updateParam((prev) => ({ ...prev, min: toNumber(e.target.value) }))}
            />
          </label>
          <label>
            Max
            <input
              type="number"
              step="any"
              value={param.max ?? ''}
              onChange={(e) => updateParam((prev) => ({ ...prev, max: toNumber(e.target.value) }))}
            />
          </label>
          <label>
            Step
            <input
              type="number"
              step="any"
              value={param.step ?? ''}
              onChange={(e) => updateParam((prev) => ({ ...prev, step: toNumber(e.target.value) }))}
            />
          </label>
        </div>
      ) : (
        <div className="parameter-card__single">
          <label>
            Fixed value
            <input
              type="number"
              step="any"
              value={param.value ?? ''}
              onChange={(e) => updateParam((prev) => ({ ...prev, value: toNumber(e.target.value) }))}
            />
          </label>
        </div>
      )}

      <p className="parameter-card__meta">
        {param.enabled
          ? `Searching from ${param.min ?? '-'} to ${param.max ?? '-'} with step ${param.step ?? '-'}`
          : `Locked at ${param.value ?? '-'} for baseline validation`}
      </p>
    </article>
  )
}

export default function OptimizationPage(): JSX.Element {
  const spaces = useFetch<OptimizationSpaceList>('/optimization/spaces')

  const strategyIds = useMemo(() => (spaces.data?.items || []).map((item) => item.strategy_id), [spaces.data])

  const [selectedStrategy, setSelectedStrategy] = useState('')
  const [draft, setDraft] = useState<OptimizationSpace | null>(null)
  const [preview, setPreview] = useState<OptimizationSpacePreview | null>(null)
  const [message, setMessage] = useState('')
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!selectedStrategy && strategyIds.length > 0) {
      setSelectedStrategy(strategyIds[0])
    }
  }, [strategyIds, selectedStrategy])

  useEffect(() => {
    async function loadDetail(): Promise<void> {
      if (!selectedStrategy) {
        return
      }
      try {
        const detail = await apiRequest<OptimizationSpaceDetail>(`/optimization/spaces/${selectedStrategy}`)
        setDraft(detail.space)
        setPreview({
          strategy_id: detail.strategy_id,
          source: detail.preview.source,
          search_mode: detail.preview.search_mode,
          total_candidates: detail.preview.total_candidates,
          raw_total_candidates: detail.preview.raw_total_candidates,
          truncated: detail.preview.truncated,
          space_summary: detail.preview.space_summary,
          sample_candidates: [],
        })
        setMessage('')
      } catch (err) {
        setMessage(String(err))
      }
    }

    void loadDetail()
  }, [selectedStrategy])

  function updateParam(name: string, updater: (prev: OptimizationParam) => OptimizationParam): void {
    setDraft((prev) => {
      if (!prev) {
        return prev
      }
      return {
        ...prev,
        parameters: {
          ...prev.parameters,
          [name]: updater(prev.parameters[name]),
        },
      }
    })
  }

  async function runPreview(): Promise<void> {
    if (!selectedStrategy || !draft) {
      return
    }
    setLoadingPreview(true)
    setMessage('')
    try {
      const out = await apiRequest<OptimizationSpacePreview>(`/optimization/preview/${selectedStrategy}`, {
        method: 'POST',
        body: JSON.stringify(draft),
      })
      setPreview(out)
    } catch (err) {
      setMessage(String(err))
    } finally {
      setLoadingPreview(false)
    }
  }

  async function saveSpace(): Promise<void> {
    if (!selectedStrategy || !draft) {
      return
    }
    setSaving(true)
    setMessage('')
    try {
      const out = await apiRequest<OptimizationSpaceDetail>(`/optimization/spaces/${selectedStrategy}`, {
        method: 'PUT',
        body: JSON.stringify(draft),
      })
      setDraft(out.space)
      setPreview({
        strategy_id: out.strategy_id,
        source: out.preview.source,
        search_mode: out.preview.search_mode,
        total_candidates: out.preview.total_candidates,
        raw_total_candidates: out.preview.raw_total_candidates,
        truncated: out.preview.truncated,
        space_summary: out.preview.space_summary,
        sample_candidates: [],
      })
      setMessage('Optimization space saved.')
    } catch (err) {
      setMessage(String(err))
    } finally {
      setSaving(false)
    }
  }

  const enabledCount = countEnabled(draft)
  const totalParams = draft ? Object.keys(draft.parameters).length : 0

  return (
    <main className="page">
      <PageHeader
        eyebrow="Build"
        title="Optimization panel"
        description={<p>Shape the search space for each strategy, estimate combinatorial cost, and lock core parameters when needed.</p>}
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/simulations">
              Open simulations
            </Link>
            <button onClick={() => void runPreview()} disabled={loadingPreview || !draft}>
              {loadingPreview ? 'Previewing...' : 'Preview space'}
            </button>
            <button onClick={() => void saveSpace()} disabled={saving || !draft}>
              {saving ? 'Saving...' : 'Save space'}
            </button>
          </div>
        }
      />

      <section className="stat-grid">
        <StatCard label="Strategies" value={String(strategyIds.length)} detail="Strategies with a declared optimization space." />
        <StatCard label="Selected" value={selectedStrategy || '-'} tone="accent" detail="Active parameter schema under editing." />
        <StatCard label="Search params" value={String(enabledCount)} detail={`${totalParams - enabledCount} fixed parameters`} />
        <StatCard
          label="Preview candidates"
          value={preview ? String(preview.total_candidates) : '-'}
          detail={
            preview ? `Raw ${preview.raw_total_candidates}${preview.truncated ? ' | truncated' : ''}` : 'Run preview to estimate search load.'
          }
        />
      </section>

      <section className="panel-grid">
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Search controller</p>
              <h2>Global search config</h2>
            </div>
            <Badge label={draft?.search_mode || 'n/a'} tone="neutral" />
          </div>

          <div className="form-grid">
            <label>
              Strategy
              <select id="strategy-select" value={selectedStrategy} onChange={(e) => setSelectedStrategy(e.target.value)}>
                {strategyIds.map((id) => (
                  <option key={id} value={id}>
                    {id}
                  </option>
                ))}
              </select>
            </label>

            {draft ? (
              <>
                <label>
                  Search mode
                  <select
                    value={draft.search_mode}
                    onChange={(e) => setDraft({ ...draft, search_mode: e.target.value as 'grid' | 'random' })}
                  >
                    <option value="grid">grid</option>
                    <option value="random">random</option>
                  </select>
                </label>
                <label>
                  Max combinations
                  <input
                    type="number"
                    value={draft.max_combinations}
                    onChange={(e) => setDraft({ ...draft, max_combinations: toNumber(e.target.value) })}
                  />
                </label>
                <label>
                  Seed
                  <input
                    type="number"
                    value={draft.seed || 0}
                    onChange={(e) => setDraft({ ...draft, seed: toNumber(e.target.value) })}
                  />
                </label>
                <label className="parameter-card__row">
                  <span>Shuffle candidates</span>
                  <input
                    type="checkbox"
                    checked={Boolean(draft.shuffle)}
                    onChange={(e) => setDraft({ ...draft, shuffle: e.target.checked })}
                  />
                </label>
              </>
            ) : null}
          </div>

          {message ? <p className={message.includes('saved') ? 'subtle-text' : 'error'}>{message}</p> : null}
          {spaces.error ? <p className="error">{spaces.error}</p> : null}
          {!draft && !spaces.loading ? <p>No optimization spaces found.</p> : null}
        </section>

        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Preview</p>
              <h2>Search cardinality</h2>
            </div>
          </div>

          {preview ? (
            <div className="section-stack">
              <div className="result-grid">
                <div>
                  <span>Visible candidates</span>
                  <strong>{preview.total_candidates}</strong>
                </div>
                <div>
                  <span>Raw candidates</span>
                  <strong>{preview.raw_total_candidates}</strong>
                </div>
                <div>
                  <span>Source</span>
                  <strong>{preview.source}</strong>
                </div>
                <div>
                  <span>Truncated</span>
                  <strong>{preview.truncated ? 'Yes' : 'No'}</strong>
                </div>
              </div>

              <div className="card">
                <h3>Space summary</h3>
                <pre>{JSON.stringify(preview.space_summary, null, 2)}</pre>
              </div>
            </div>
          ) : (
            <p className="subtle-text">Preview data will appear here after the first load or manual refresh.</p>
          )}
        </section>
      </section>

      {draft ? (
        <section className="surface-card">
          <div className="surface-card__header">
            <div>
              <p className="surface-card__eyebrow">Parameters</p>
              <h2>Optimization space editor</h2>
            </div>
          </div>
          <div className="parameter-grid">
            {Object.entries(draft.parameters).map(([name, param]) => (
              <ParameterCard key={name} name={name} param={param} updateParam={(updater) => updateParam(name, updater)} />
            ))}
          </div>
        </section>
      ) : null}
    </main>
  )
}
