export type JsonRecord = Record<string, unknown>

export type ListResponse<T> = {
  total: number
  limit: number
  offset: number
  items: T[]
}

export type RunItem = {
  run_id: string
  external_run_id?: string | null
  filename?: string
  run_at?: string | null
  status?: string
  strategy?: string | null
  strategy_id?: string | null
  market?: string | null
  symbol?: string | null
  timeframe?: string | null
  metrics?: JsonRecord
}

export type ManifestItem = {
  manifest_id: string
  filename?: string
  created_at?: string | null
  status?: string
  rows?: number
  ok?: number
  failed?: number
}

export type HealthResponse = {
  status: string
}

export type RunDetailResponse = {
  run_id: string
  payload: JsonRecord
}

export type ManifestDetailResponse = {
  manifest_id: string
  payload: JsonRecord
}

export type TableColumn<T> = {
  key: string
  label: string
  render?: (row: T) => React.ReactNode
}
