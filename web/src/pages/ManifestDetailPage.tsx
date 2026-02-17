import { Link, useParams } from 'react-router-dom'

import { useFetch } from '../api'
import Table from '../components/Table'
import type { JsonRecord, ManifestDetailResponse } from '../types'

type ManifestResult = {
  market?: string
  symbol?: string
  timeframe?: string
  status?: string
  output_file?: string
  error?: string
}

export default function ManifestDetailPage(): JSX.Element {
  const { manifestId = '' } = useParams()
  const manifest = useFetch<ManifestDetailResponse>(`/ingest-manifests/${manifestId}`)

  if (manifest.loading) {
    return (
      <main>
        <p>Loading manifest detail...</p>
      </main>
    )
  }

  if (manifest.error) {
    return (
      <main>
        <p className="error">{manifest.error}</p>
        <p>
          <Link to="/">Back to dashboard</Link>
        </p>
      </main>
    )
  }

  const payload = (manifest.data?.payload || {}) as JsonRecord
  const results = ((payload.results as ManifestResult[] | undefined) || []) as ManifestResult[]

  return (
    <main>
      <header>
        <h1>Manifest detail: {manifest.data?.manifest_id}</h1>
        <p>
          <Link to="/">Back to dashboard</Link>
        </p>
      </header>

      <section>
        <h2>Summary</h2>
        <div className="card">
          <p>
            <strong>Status:</strong> {String(payload.status || '-')}
          </p>
          <p>
            <strong>Created at:</strong> {String(payload.created_at || '-')}
          </p>
          <p>
            <strong>Rows:</strong> {results.length}
          </p>
        </div>
      </section>

      <section>
        <h2>Entries</h2>
        <Table<ManifestResult>
          columns={[
            { key: 'market', label: 'Market' },
            { key: 'symbol', label: 'Symbol' },
            { key: 'timeframe', label: 'Timeframe' },
            { key: 'status', label: 'Status' },
            { key: 'output_file', label: 'Output file' },
            { key: 'error', label: 'Error' }
          ]}
          rows={results}
          emptyLabel="No ingest rows available."
        />
      </section>

      <section>
        <h2>Raw payload</h2>
        <pre>{JSON.stringify(payload, null, 2)}</pre>
      </section>
    </main>
  )
}
