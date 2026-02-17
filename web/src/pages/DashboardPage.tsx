import { Link } from 'react-router-dom'

import { useFetch } from '../api'
import Table from '../components/Table'
import type { HealthResponse, ListResponse, ManifestItem, RunItem } from '../types'

export default function DashboardPage(): JSX.Element {
  const health = useFetch<HealthResponse>('/health')
  const runs = useFetch<ListResponse<RunItem>>('/runs?limit=10')
  const manifests = useFetch<ListResponse<ManifestItem>>('/ingest-manifests?limit=10')

  return (
    <main>
      <header>
        <h1>cbot-farm dashboard</h1>
        <p>Runs and ingestion overview. <Link to="/optimization">Open optimization panel</Link></p>
      </header>

      <section className="kpis">
        <div className="card">
          <h3>API health</h3>
          <p>{health.loading ? 'loading...' : health.data?.status || health.error}</p>
        </div>
        <div className="card">
          <h3>Total runs</h3>
          <p>{runs.loading ? 'loading...' : runs.data?.total ?? '-'}</p>
        </div>
        <div className="card">
          <h3>Total manifests</h3>
          <p>{manifests.loading ? 'loading...' : manifests.data?.total ?? '-'}</p>
        </div>
      </section>

      <section>
        <h2>Latest runs</h2>
        {runs.error ? <p className="error">{runs.error}</p> : null}
        <Table<RunItem>
          columns={[
            {
              key: 'run_id',
              label: 'Run ID',
              render: (row) => <Link to={`/runs/${row.run_id}`}>{row.run_id}</Link>
            },
            { key: 'run_at', label: 'Date' },
            { key: 'strategy_id', label: 'Strategy' },
            { key: 'market', label: 'Market' },
            { key: 'symbol', label: 'Symbol' },
            { key: 'timeframe', label: 'TF' },
            { key: 'status', label: 'Status' }
          ]}
          rows={runs.data?.items || []}
        />
      </section>

      <section>
        <h2>Latest ingest manifests</h2>
        {manifests.error ? <p className="error">{manifests.error}</p> : null}
        <Table<ManifestItem>
          columns={[
            {
              key: 'manifest_id',
              label: 'Manifest ID',
              render: (row) => (
                <Link to={`/ingestion/${row.manifest_id}`}>{row.manifest_id}</Link>
              )
            },
            { key: 'created_at', label: 'Date' },
            { key: 'status', label: 'Status' },
            { key: 'rows', label: 'Rows' },
            { key: 'ok', label: 'OK' },
            { key: 'failed', label: 'Failed' }
          ]}
          rows={manifests.data?.items || []}
        />
      </section>
    </main>
  )
}
