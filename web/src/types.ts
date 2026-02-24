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

export type BatchItem = {
  batch_id: string
  created_at?: string | null
  strategy?: string | null
  max_retries?: number | null
  scenarios?: number
  total_reports?: number
  promoted_count?: number
  best_return_pct?: number | null
}

export type BatchBestRecord = {
  report?: string
  iteration?: number
  params?: JsonRecord
  metrics?: JsonRecord
  score_return_minus_dd?: number
  promoted?: boolean
  candidate_index?: number
  total_candidates?: number
}

export type BatchScenario = {
  name: string
  market?: string
  symbol?: string
  timeframe?: string
  iterations?: number
  reports?: number
  promoted_count?: number
  best?: BatchBestRecord
  best_run_id?: string | null
  best_equity_curve?: Array<{ x: number; equity: number }>
  best_trades_count?: number | null
}

export type BatchDetailResponse = {
  batch_id: string
  summary: JsonRecord
  scenarios: BatchScenario[]
}

export type SimOptionsResponse = {
  strategies: Record<string, string>
  markets: Record<string, { symbols: string[]; timeframes: string[] }>
  defaults: {
    strategy_id: string
    iterations: number
    skip_ingest: boolean
  }
}

export type SimRunResponse = {
  simulation: {
    run_id: string
    external_run_id: string
    report_path: string
    metrics: JsonRecord
    gates: JsonRecord
    status: string
  }
}

export type WorkflowRunRef = {
  run_id?: string
  created_at?: string | null
  metrics?: JsonRecord
}

export type WorkflowItem = {
  strategy_id: string
  display_name: string
  state: string
  updated_at?: string | null
  allowed_transitions: string[]
  last_run?: WorkflowRunRef | null
  history_size?: number
}

export type WorkflowBoardResponse = {
  states: string[]
  counts: Record<string, number>
  items: WorkflowItem[]
  updated_at?: string | null
}

export type WorkflowTransitionResponse = {
  strategy: JsonRecord
}
