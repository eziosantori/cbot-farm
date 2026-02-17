export type JsonPrimitive = string | number | boolean | null
export interface JsonRecord {
  [key: string]: JsonValue
}
export type JsonValue = JsonPrimitive | JsonRecord | JsonValue[]

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

export type OptimizationParam = {
  enabled: boolean
  type: 'int' | 'float'
  min?: number
  max?: number
  step?: number
  value?: number
}

export type OptimizationSpace = {
  search_mode: 'grid' | 'random'
  max_combinations: number
  shuffle?: boolean
  seed?: number
  parameters: Record<string, OptimizationParam>
}

export type OptimizationSpacePreview = {
  strategy_id: string
  source: string
  search_mode: string
  total_candidates: number
  raw_total_candidates: number
  truncated: boolean
  space_summary: JsonRecord
  sample_candidates: JsonRecord[]
}

export type OptimizationSpaceDetail = {
  strategy_id: string
  space: OptimizationSpace
  preview: {
    total_candidates: number
    raw_total_candidates: number
    truncated: boolean
    search_mode: string
    source: string
    space_summary: JsonRecord
  }
}

export type OptimizationSpaceList = {
  total: number
  items: Array<{
    strategy_id: string
    parameters_total: number
    parameters_enabled: number
    search_mode: string
    max_combinations: number
  }>
}
