import { Link } from 'react-router-dom'

import { useFetch } from '../api'
import Badge from '../components/Badge'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Table from '../components/Table'
import type { BatchItem, ListResponse } from '../types'

function fmtNum(raw: number | null | undefined, suffix = ''): string {
  if (typeof raw !== 'number' || Number.isNaN(raw)) {
    return '-'
  }
  return `${raw.toFixed(2)}${suffix}`
}

export default function BatchesPage(): JSX.Element {
  const batches = useFetch<ListResponse<BatchItem>>('/batches?limit=50')
  const items = batches.data?.items || []
  const totalReports = items.reduce((acc, item) => acc + (item.total_reports || 0), 0)
  const totalPromoted = items.reduce((acc, item) => acc + (item.promoted_count || 0), 0)
  const bestBatch = items.reduce<BatchItem | null>((best, item) => {
    if (!best) {
      return item
    }
    return (item.best_return_pct || Number.NEGATIVE_INFINITY) > (best.best_return_pct || Number.NEGATIVE_INFINITY)
      ? item
      : best
  }, null)

  return (
    <main className="page">
      <PageHeader
        eyebrow="Observe"
        title="Batch analytics"
        description={<p>Review optimization batches as operator-ready summaries instead of raw JSON artifacts.</p>}
        actions={
          <div className="quick-actions">
            <Link className="quick-actions__link" to="/simulations">
              Launch simulation
            </Link>
            <Link className="quick-actions__link" to="/workflow">
              Open workflow
            </Link>
          </div>
        }
      />

      <section className="stat-grid">
        <StatCard label="Visible batches" value={String(items.length)} detail="Latest 50 batch summaries from reports." />
        <StatCard label="Total reports" value={String(totalReports)} detail="Aggregated reports across the current page." />
        <StatCard label="Promoted candidates" value={String(totalPromoted)} detail="Runs that passed the current promotion rules." />
        <StatCard
          label="Best batch return"
          value={fmtNum(bestBatch?.best_return_pct, '%')}
          tone="accent"
          detail={bestBatch?.batch_id || 'No batch available yet'}
        />
      </section>

      <section className="surface-card">
        <div className="surface-card__header">
          <div>
            <p className="surface-card__eyebrow">Latest campaign output</p>
            <h2>Batch ledger</h2>
          </div>
          <Badge label={batches.loading ? 'Loading' : `${items.length} rows`} tone="neutral" />
        </div>
        {batches.error ? <p className="error">{batches.error}</p> : null}
        <Table<BatchItem>
          columns={[
            {
              key: 'batch_id',
              label: 'Batch',
              render: (row) => <Link to={`/batches/${row.batch_id}`}>{row.batch_id}</Link>,
            },
            {
              key: 'strategy',
              label: 'Strategy',
              render: (row) => row.strategy || '-',
            },
            {
              key: 'scenarios',
              label: 'Scenarios',
              render: (row) => String(row.scenarios ?? '-'),
            },
            {
              key: 'total_reports',
              label: 'Reports',
              render: (row) => String(row.total_reports ?? '-'),
            },
            {
              key: 'promoted_count',
              label: 'Promoted',
              render: (row) => String(row.promoted_count ?? '-'),
            },
            {
              key: 'best_return_pct',
              label: 'Best Return %',
              render: (row) => fmtNum(row.best_return_pct, '%'),
            },
          ]}
          rows={items}
          emptyLabel={batches.loading ? 'Loading batches...' : 'No batches found.'}
        />
      </section>

      <section className="card-grid">
        {items.slice(0, 6).map((item) => (
          <Link className="insight-card" key={item.batch_id} to={`/batches/${item.batch_id}`}>
            <div className="insight-card__head">
              <Badge label={item.strategy || 'unknown strategy'} tone="accent" />
              <span className="insight-card__meta">{item.batch_id}</span>
            </div>
            <strong>{fmtNum(item.best_return_pct, '%')} best return</strong>
            <p>
              {item.scenarios ?? 0} scenarios, {item.total_reports ?? 0} reports, {item.promoted_count ?? 0} promoted
              candidates.
            </p>
          </Link>
        ))}
      </section>
    </main>
  )
}
