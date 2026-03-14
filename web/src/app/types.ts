export type SourceMap = Record<string, string[]>

export type SourceErrorDetail = {
  kind: string
  source: string
  error: string
  hint: string
}

export type SourceHealthItem = {
  kind: string
  source: string
  count: number
  last_seen: string
  last_run_id: string
  last_error: string
  hint: string
}

export type SourceHealthStatus = "healthy" | "failing"

export type UnifiedSourceRow = {
  key: string
  type: string
  type_label: string
  source: string
  count: number
  health: SourceHealthStatus
  last_error: string
  last_seen: string
  hint: string
  identity_title: string
  identity_subtitle: string
  preview_status: "ready" | "no_items" | "preview_unavailable"
  preview_url: string | null
  preview_title: string
  preview_description: string
  preview_image_url: string | null
  preview_host: string
  preview_published_at: string
  can_edit: boolean
  can_delete: boolean
}

export type RunStatus = {
  active: { run_id: string; started_at: string } | null
  latest: {
    run_id: string
    status: string
    started_at: string
    source_error_count: number
    summary_error_count: number
  } | null
  latest_completed: {
    run_id: string
    status: string
    started_at: string
    source_error_count: number
    summary_error_count: number
    source_errors: SourceErrorDetail[]
  } | null
}

export type RunProgress = {
  available: boolean
  run_id: string
  pipeline_run_id: string
  mode: string
  stage: string
  stage_label: string
  message: string
  stage_detail: string
  elapsed_s: number
  percent: number | null
  status: string
  is_active: boolean
  started_at: string
  updated_at: string
  details: Record<string, unknown>
  event_index: number
}

export type HistoryItem = {
  id: string
  created_at: string
  action: string
  details: Record<string, unknown>
}

export type PreflightCheck = {
  id: string
  label: string
  status: "pass" | "warn" | "fail"
  detail: string
  hint: string
  required: boolean
}

export type PreflightReport = {
  generated_at_utc: string
  ok: boolean
  pass_count: number
  warn_count: number
  fail_count: number
  checks: PreflightCheck[]
}

export type OnboardingStep = {
  id: string
  label: string
  status: "complete" | "pending"
  completed_at: string
  detail: string
}

export type OnboardingStatus = {
  generated_at_utc: string
  lifecycle: "needs_setup" | "ready"
  steps: OnboardingStep[]
  progress: { completed: number; total: number }
  preflight: {
    ok: boolean
    pass_count: number
    warn_count: number
    fail_count: number
  }
  latest_completed: {
    run_id: string
    status: string
    started_at: string
    source_error_count: number
    summary_error_count: number
  } | null
}

export type ScheduleConfig = {
  enabled: boolean
  cadence: "daily" | "hourly"
  time_local: string
  hourly_minute: number
  quiet_hours_enabled: boolean
  quiet_start_local: string
  quiet_end_local: string
  timezone: string
}

export type ScheduleStatus = {
  enabled: boolean
  cadence: "daily" | "hourly"
  time_local: string
  hourly_minute: number
  quiet_hours_enabled: boolean
  quiet_start_local: string
  quiet_end_local: string
  timezone: string
  scheduler_status: string
  quiet_hours_active: boolean
  next_run_at: string
  last_triggered_at: string
  last_attempted_run_id: string
  last_result: string
  last_error: string
  active_run_id: string
}

export type SourcePack = {
  id: string
  name: string
  description: string
  item_count: number
}

export type PreviewResult = {
  run_id: string
  status: string
  source_error_count: number
  summary_error_count: number
  source_errors: string[]
  summary_errors: string[]
  source_count: number
  must_read_count: number
  skim_count: number
  video_count: number
  telegram_messages: string[]
  obsidian_note: string
}

export type TimelineRun = {
  run_id: string
  status: string
  started_at: string
  window_start: string
  window_end: string
  event_count: number
}

export type TimelineEvent = {
  id: number
  run_id: string
  event_index: number
  ts_utc: string
  stage: string
  severity: "info" | "warn" | "error"
  message: string
  elapsed_s: number
  details: Record<string, unknown>
}

export type TimelineSummary = {
  run_id: string
  status: string
  started_at: string
  event_count: number
  error_event_count: number
  warn_event_count: number
  duration_s: number
  last_stage: string
  last_message: string
  final_item_count: number
  must_read_count: number
  skim_count: number
  video_count: number
  source_error_count: number
  summary_error_count: number
  mode?: {
    name: string
    use_last_completed_window: boolean
    only_new: boolean
    allow_seen_fallback: boolean
  }
  filter_funnel?: {
    fetched: number
    post_window: number
    post_seen: number
    post_block: number
    selected: number
  }
  strictness_score?: number
  strictness_level?: "low" | "medium" | "high" | string
  restriction_reasons?: Array<{
    key: string
    label: string
    dropped: number
    ratio_pct: number
  }>
  recommendations?: string[]
}

export type TimelineNote = {
  id: number
  run_id: string
  created_at_utc: string
  author: string
  note: string
  labels: string[]
  actions: string[]
}

export type RunItem = {
  run_id: string
  item_id: string
  section: string
  section_rank: number
  source_family: string
  score_total: number
  summary: string
  tags: string[]
  topic_tags: string[]
  format_tags: string[]
  url: string
  title: string
  source: string
  author: string
  published_at: string
  type: string
  description: string
}

export type RunArtifact = {
  id: number
  run_id: string
  channel: string
  artifact_type: string
  storage_path: string
  preview_mode: boolean
  chunk_count: number
  created_at: string
  content: string
}

export type FeedbackSummary = {
  ratings: Array<{ rating: number; count: number }>
  top_positive: Array<{ feature_type: string; feature_key: string; weight: number }>
  top_negative: Array<{ feature_type: string; feature_key: string; weight: number }>
  recent: Array<{
    id: number
    run_id: string
    item_id: string
    rating: number
    label: string
    comment: string
    created_at: string
  }>
}

export type RunPolicy = {
  default_mode: "fresh_only" | "balanced" | "replay_recent" | "backfill"
  allow_run_override: boolean
  seen_reset_guard: "confirm" | "disabled"
}

export type SaveAction =
  | ""
  | "source-add"
  | "source-remove"
  | "source-feedback"
  | "onboarding-preflight"
  | "source-pack"
  | "schedule-save"
  | "profile-validate"
  | "profile-diff"
  | "profile-save"
  | "run-policy-save"
  | "profile-feedback-refresh"
  | "timeline-refresh"
  | "timeline-export"
  | "timeline-note"
  | "timeline-item-feedback"
  | "seen-reset-preview"
  | "seen-reset-apply"
  | "rollback"

export type Notice = { kind: "ok" | "error"; text: string }
export type NoticeScope = "global" | "run" | "onboarding" | "sources" | "profile" | "schedule" | "timeline" | "history"

export type ConsoleSurface = "dashboard" | "run" | "onboarding" | "sources" | "profile" | "schedule" | "timeline" | "history"
