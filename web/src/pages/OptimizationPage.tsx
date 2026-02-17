import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
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

export default function OptimizationPage(): JSX.Element {
  const spaces = useFetch<OptimizationSpaceList>('/optimization/spaces')

  const strategyIds = useMemo(
    () => (spaces.data?.items || []).map((item) => item.strategy_id),
    [spaces.data]
  )

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
        const detail = await apiRequest<OptimizationSpaceDetail>(
          `/optimization/spaces/${selectedStrategy}`
        )
        setDraft(detail.space)
        setPreview({
          strategy_id: detail.strategy_id,
          source: detail.preview.source,
          search_mode: detail.preview.search_mode,
          total_candidates: detail.preview.total_candidates,
          raw_total_candidates: detail.preview.raw_total_candidates,
          truncated: detail.preview.truncated,
          space_summary: detail.preview.space_summary,
          sample_candidates: []
        })
        setMessage('')
      } catch (err) {
        setMessage(String(err))
      }
    }

    void loadDetail()
  }, [selectedStrategy])

  function updateParam(
    name: string,
    updater: (prev: OptimizationParam) => OptimizationParam
  ): void {
    setDraft((prev) => {
      if (!prev) {
        return prev
      }
      return {
        ...prev,
        parameters: {
          ...prev.parameters,
          [name]: updater(prev.parameters[name])
        }
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
      const out = await apiRequest<OptimizationSpacePreview>(
        `/optimization/preview/${selectedStrategy}`,
        {
          method: 'POST',
          body: JSON.stringify(draft)
        }
      )
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
      const out = await apiRequest<OptimizationSpaceDetail>(
        `/optimization/spaces/${selectedStrategy}`,
        {
          method: 'PUT',
          body: JSON.stringify(draft)
        }
      )
      setDraft(out.space)
      setPreview({
        strategy_id: out.strategy_id,
        source: out.preview.source,
        search_mode: out.preview.search_mode,
        total_candidates: out.preview.total_candidates,
        raw_total_candidates: out.preview.raw_total_candidates,
        truncated: out.preview.truncated,
        space_summary: out.preview.space_summary,
        sample_candidates: []
      })
      setMessage('Optimization space saved.')
    } catch (err) {
      setMessage(String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <main>
      <header>
        <h1>Optimization panel</h1>
        <p>
          Configure parameter space and preview search cardinality.{' '}
          <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section className="card">
        <label htmlFor="strategy-select"><strong>Strategy</strong></label>
        <div>
          <select
            id="strategy-select"
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
          >
            {strategyIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>
      </section>

      {draft ? (
        <>
          <section className="card">
            <h2>Search config</h2>
            <div className="form-grid">
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
                Shuffle
                <input
                  type="checkbox"
                  checked={Boolean(draft.shuffle)}
                  onChange={(e) => setDraft({ ...draft, shuffle: e.target.checked })}
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
            </div>
          </section>

          <section>
            <h2>Parameters</h2>
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Enabled</th>
                  <th>Type</th>
                  <th>Min</th>
                  <th>Max</th>
                  <th>Step</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(draft.parameters).map(([name, param]) => (
                  <tr key={name}>
                    <td>{name}</td>
                    <td>
                      <input
                        type="checkbox"
                        checked={param.enabled}
                        onChange={(e) =>
                          updateParam(name, (prev) => ({ ...prev, enabled: e.target.checked }))
                        }
                      />
                    </td>
                    <td>
                      <select
                        value={param.type}
                        onChange={(e) =>
                          updateParam(name, (prev) => ({
                            ...prev,
                            type: e.target.value as 'int' | 'float'
                          }))
                        }
                      >
                        <option value="int">int</option>
                        <option value="float">float</option>
                      </select>
                    </td>
                    <td>
                      <input
                        type="number"
                        step="any"
                        value={param.min ?? ''}
                        disabled={!param.enabled}
                        onChange={(e) =>
                          updateParam(name, (prev) => ({ ...prev, min: toNumber(e.target.value) }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="any"
                        value={param.max ?? ''}
                        disabled={!param.enabled}
                        onChange={(e) =>
                          updateParam(name, (prev) => ({ ...prev, max: toNumber(e.target.value) }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="any"
                        value={param.step ?? ''}
                        disabled={!param.enabled}
                        onChange={(e) =>
                          updateParam(name, (prev) => ({ ...prev, step: toNumber(e.target.value) }))
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="any"
                        value={param.value ?? ''}
                        disabled={param.enabled}
                        onChange={(e) =>
                          updateParam(name, (prev) => ({ ...prev, value: toNumber(e.target.value) }))
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <button onClick={() => void runPreview()} disabled={loadingPreview}>
              {loadingPreview ? 'Previewing...' : 'Preview combinations'}
            </button>
            <button onClick={() => void saveSpace()} disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
            </button>
            {preview ? (
              <p>
                Candidates: {preview.total_candidates} (raw {preview.raw_total_candidates}){' '}
                {preview.truncated ? '(truncated)' : ''}
              </p>
            ) : null}
            {message ? <p>{message}</p> : null}
          </section>
        </>
      ) : (
        <section className="card">
          <p>{spaces.loading ? 'Loading optimization spaces...' : 'No optimization spaces found.'}</p>
          {spaces.error ? <p className="error">{spaces.error}</p> : null}
        </section>
      )}
    </main>
  )
}
