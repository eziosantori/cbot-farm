import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, useFetch } from '../api'
import Badge from '../components/Badge'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import type { WorkflowBoardResponse, WorkflowItem, WorkflowTransitionResponse } from '../types'

function metricValue(raw: unknown, suffix = ''): string {
  if (typeof raw === 'number') {
    return `${raw.toFixed(2)}${suffix}`
  }
  if (typeof raw === 'string') {
    const n = Number(raw)
    if (Number.isFinite(n)) {
      return `${n.toFixed(2)}${suffix}`
    }
  }
  return '-'
}

function stateTone(state: string): 'neutral' | 'accent' | 'success' | 'warning' {
  if (state === 'approved') {
    return 'success'
  }
  if (state === 'candidate' || state === 'paper') {
    return 'accent'
  }
  if (state === 'archived') {
    return 'warning'
  }
  return 'neutral'
}

function WorkflowCard({
  item,
  busyId,
  onTransition,
}: {
  item: WorkflowItem
  busyId: string
  onTransition: (strategyId: string, toState: string) => Promise<void>
}): JSX.Element {
  return (
    <article className="workflow-card">
      <div className="workflow-card__head">
        <div>
          <p className="workflow-card__id">{item.strategy_id}</p>
          <h3>{item.display_name}</h3>
        </div>
        <Badge label={item.state} tone={stateTone(item.state)} />
      </div>

      <div className="workflow-card__metrics">
        <div>
          <span>Return</span>
          <strong>{metricValue(item.last_run?.metrics?.total_return_pct, '%')}</strong>
        </div>
        <div>
          <span>Sharpe</span>
          <strong>{metricValue(item.last_run?.metrics?.sharpe)}</strong>
        </div>
        <div>
          <span>Max DD</span>
          <strong>{metricValue(item.last_run?.metrics?.max_drawdown_pct, '%')}</strong>
        </div>
        <div>
          <span>OOS</span>
          <strong>{metricValue(item.last_run?.metrics?.oos_degradation_pct, '%')}</strong>
        </div>
      </div>

      <p className="workflow-card__run">
        <strong>Last run:</strong>{' '}
        {item.last_run?.run_id ? <Link to={`/runs/${item.last_run.run_id}`}>{item.last_run.run_id}</Link> : 'No run linked yet'}
      </p>

      <div className="workflow-card__actions">
        {item.allowed_transitions.length === 0 ? (
          <span className="workflow-card__empty">No allowed transition</span>
        ) : (
          item.allowed_transitions.map((toState) => (
            <button
              key={toState}
              disabled={busyId === item.strategy_id}
              onClick={() => void onTransition(item.strategy_id, toState)}
            >
              Move to {toState}
            </button>
          ))
        )}
      </div>
    </article>
  )
}

export default function WorkflowPage(): JSX.Element {
  const [refreshToken, setRefreshToken] = useState(0)
  const board = useFetch<WorkflowBoardResponse>(`/strategy-workflow?refresh=${refreshToken}`)
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
      setRefreshToken((value) => value + 1)
    } catch (err) {
      setError(String(err))
    } finally {
      setBusyId('')
    }
  }

  return (
    <main className="page">
      <PageHeader
        eyebrow="Govern"
        title="Strategy workflow"
        description={<p>Track lifecycle state, review last-run quality, and move strategies through the lab with guarded transitions.</p>}
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/intake">
              Create intake
            </Link>
            <Link className="quick-actions__link" to="/batches">
              Open batches
            </Link>
          </div>
        }
      />

      <section className="stat-grid">
        {(board.data?.states || []).map((state) => (
          <StatCard
            key={state}
            label={state}
            value={String(board.data?.counts?.[state] ?? 0)}
            tone={state === 'approved' ? 'accent' : 'default'}
            detail="Strategies currently in this lifecycle stage."
          />
        ))}
      </section>

      {error ? <p className="error">{error}</p> : null}

      <section className="workflow-board">
        {(board.data?.states || []).map((state) => {
          const items = grouped.get(state) || []
          return (
            <section className="workflow-column" key={state}>
              <div className="workflow-column__header">
                <Badge label={state} tone={stateTone(state)} />
                <span>{items.length}</span>
              </div>
              {!items.length ? <p className="workflow-column__empty">No strategies in this state.</p> : null}
              {items.map((item) => (
                <WorkflowCard key={item.strategy_id} item={item} busyId={busyId} onTransition={transition} />
              ))}
            </section>
          )
        })}
      </section>
    </main>
  )
}
