import { Link } from 'react-router-dom'

import { useFetch } from '../api'
import Table from '../components/Table'
import type { BatchItem, ListResponse } from '../types'

function fmtNum(raw: number | null | undefined): string {
  if (typeof raw !== 'number' || Number.isNaN(raw)) {
    return '-'
  }
  return raw.toFixed(2)
}

export default function BatchesPage(): JSX.Element {
  const batches = useFetch<ListResponse<BatchItem>>('/batches?limit=50')

  return (
    <main>
      <header>
        <h1>Batch analytics</h1>
        <p>
          Batch summaries with quick navigation to best runs. <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section>
        <h2>Available batches</h2>
        {batches.error ? <p className="error">{batches.error}</p> : null}
        <Table<BatchItem>
          columns={[
            {
              key: 'batch_id',
              label: 'Batch ID',
              render: (row) => <Link to={`/batches/${row.batch_id}`}>{row.batch_id}</Link>
            },
            { key: 'created_at', label: 'Created At' },
            { key: 'strategy', label: 'Strategy' },
            {
              key: 'max_retries',
              label: 'Max Retries',
              render: (row) => String(row.max_retries ?? '-')
            },
            {
              key: 'scenarios',
              label: 'Scenarios',
              render: (row) => String(row.scenarios ?? '-')
            },
            {
              key: 'total_reports',
              label: 'Reports',
              render: (row) => String(row.total_reports ?? '-')
            },
            {
              key: 'promoted_count',
              label: 'Promoted',
              render: (row) => String(row.promoted_count ?? '-')
            },
            {
              key: 'best_return_pct',
              label: 'Best Return %',
              render: (row) => fmtNum(row.best_return_pct)
            }
          ]}
          rows={batches.data?.items || []}
          emptyLabel={batches.loading ? 'Loading batches...' : 'No batches found.'}
        />
      </section>
    </main>
  )
}
