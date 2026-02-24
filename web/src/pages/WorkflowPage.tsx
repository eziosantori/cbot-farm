import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
import type { WorkflowBoardResponse, WorkflowItem, WorkflowTransitionResponse } from '../types'

function metricValue(raw: unknown): string {
  if (typeof raw === 'number') {
    return raw.toFixed(2)
  }
  if (typeof raw === 'string') {
    const n = Number(raw)
    if (Number.isFinite(n)) {
      return n.toFixed(2)
    }
  }
  return '-'
}

export default function WorkflowPage(): JSX.Element {
  const board = useFetch<WorkflowBoardResponse>('/strategy-workflow')
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')

  const grouped = useMemo(() => {
    const map = new Map<string, WorkflowItem[]>()
    for (const state of board.data?.states || []) {
      map.set(state, [])
    }
    for (const item of board.data?.items || []) {
      if (!map.has(item.state)) {
        map.set(item.state, [])
      }
      map.get(item.state)?.push(item)
    }
    return map
  }, [board.data])

  async function transition(strategyId: string, toState: string): Promise<void> {
    setBusyId(strategyId)
    setError('')
    try {
      await apiRequest<WorkflowTransitionResponse>(`/strategy-workflow/${strategyId}/transition`, {
        method: 'POST',
        body: JSON.stringify({ to_state: toState, note: 'updated from workflow UI' }),
      })
      window.location.reload()
    } catch (err) {
      setError(String(err))
    } finally {
      setBusyId('')
    }
  }

  return (
    <main>
      <header>
        <h1>Strategy workflow</h1>
        <p>
          Track lifecycle states and apply guarded transitions. <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section className="kpis">
        {(board.data?.states || []).map((state) => (
          <div className="card" key={state}>
            <h3>{state}</h3>
            <p>{String(board.data?.counts?.[state] ?? 0)}</p>
          </div>
        ))}
      </section>

      {error ? <p className="error">{error}</p> : null}

      {(board.data?.states || []).map((state) => {
        const items = grouped.get(state) || []
        return (
          <section key={state}>
            <h2>{state}</h2>
            {!items.length ? <p>No strategies in this state.</p> : null}
            {items.map((item) => (
              <div className="card" key={item.strategy_id} style={{ marginBottom: '12px' }}>
                <p>
                  <strong>{item.strategy_id}</strong> - {item.display_name}
                </p>
                <p>
                  <strong>Last run:</strong>{' '}
                  {item.last_run?.run_id ? (
                    <Link to={`/runs/${item.last_run.run_id}`}>{item.last_run.run_id}</Link>
                  ) : (
                    '-'
                  )}
                </p>
                <p>
                  <strong>Return:</strong> {metricValue(item.last_run?.metrics?.total_return_pct)} |{' '}
                  <strong>Sharpe:</strong> {metricValue(item.last_run?.metrics?.sharpe)} |{' '}
                  <strong>Max DD:</strong> {metricValue(item.last_run?.metrics?.max_drawdown_pct)} |{' '}
                  <strong>OOS:</strong> {metricValue(item.last_run?.metrics?.oos_degradation_pct)}
                </p>
                <p>
                  <strong>Transition:</strong>{' '}
                  {item.allowed_transitions.length === 0 ? (
                    'No allowed transition'
                  ) : (
                    item.allowed_transitions.map((to) => (
                      <button
                        key={to}
                        disabled={busyId === item.strategy_id}
                        onClick={() => void transition(item.strategy_id, to)}
                      >
                        {to}
                      </button>
                    ))
                  )}
                </p>
              </div>
            ))}
          </section>
        )
      })}
    </main>
  )
}
