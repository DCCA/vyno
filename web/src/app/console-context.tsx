import { createContext, useContext, type Dispatch, type ReactNode, type SetStateAction } from "react"

import type {
  ConsoleSurface,
  FeedbackSummary,
  HistoryItem,
  Notice,
  NoticeScope,
  OnboardingStatus,
  PreflightReport,
  PreviewResult,
  RunArtifact,
  RunItem,
  RunPolicy,
  RunProgress,
  RunStatus,
  SaveAction,
  ScheduleConfig,
  ScheduleStatus,
  SourceHealthItem,
  SourceMap,
  SourcePack,
  TimelineEvent,
  TimelineNote,
  TimelineRun,
  TimelineSummary,
  UnifiedSourceRow,
} from "@/app/types"

// ── Shared UI state ──

export type UiState = {
  loading: boolean
  saving: boolean
  saveAction: SaveAction
  globalNotice: Notice | null
  localNotices: Partial<Record<Exclude<NoticeScope, "global">, Notice>>
  clearScopedNotice: (scope: NoticeScope) => void
}

// ── Run domain ──

export type RunState = {
  runStatus: RunStatus | null
  runProgress: RunProgress | null
  runPolicy: RunPolicy
  setRunPolicy: Dispatch<SetStateAction<RunPolicy>>
  runNowModeOverride: string
  setRunNowModeOverride: (value: string) => void
  runNowLoading: boolean
  digestBusy: boolean
  onRunNow: () => void
  onRefreshAll: () => void
}

// ── Source domain ──

export type SourceState = {
  sources: SourceMap
  sourceTypes: string[]
  sourceType: string
  setSourceType: (value: string) => void
  sourceValue: string
  setSourceValue: (value: string) => void
  sourceSearch: string
  setSourceSearch: (value: string) => void
  sourceStatusFilter: "all" | "healthy" | "failing"
  setSourceStatusFilter: (value: "all" | "healthy" | "failing") => void
  sourceHealth: SourceHealthItem[]
  filteredUnifiedSourceRows: UnifiedSourceRow[]
  unifiedRowsVisible: UnifiedSourceRow[]
  showAllUnifiedSources: boolean
  setShowAllUnifiedSources: (value: boolean) => void
  onHandleSourceMutation: (action: "add" | "remove") => void
  onEditUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onDeleteUnifiedSourceRow: (row: UnifiedSourceRow) => void
  onSourceFeedback: (row: UnifiedSourceRow, label: string) => void
}

// ── Profile domain ──

export type ProfileState = {
  profile: Record<string, unknown> | null
  profileJson: string
  setProfileJson: (value: string) => void
  updateProfileField: (path: string, value: unknown) => void
  profileJsonParseError: string
  profileWorkspaceChangeCount: number
  localProfileDiff: Record<string, unknown>
  profileDiff: Record<string, unknown>
  profileDiffComputedAt: string
  runPolicyDirty: boolean
  runPolicyChangeCount: number
  seenResetDays: string
  setSeenResetDays: (value: string) => void
  seenResetConfirm: boolean
  setSeenResetConfirm: (value: boolean) => void
  seenResetPreviewCount: number | null
  feedbackSummary: FeedbackSummary | null
  onValidateProfile: () => void
  onComputeProfileDiff: () => void
  onSaveProfileWorkspace: () => void
  onPreviewSeenReset: () => void
  onApplySeenReset: () => void
}

// ── Schedule domain ──

export type ScheduleState = {
  scheduleDraft: ScheduleConfig
  scheduleDirty: boolean
  scheduleStatus: ScheduleStatus | null
  onChangeScheduleField: (field: keyof ScheduleConfig, value: string | boolean | number) => void
  onSaveSchedule: () => void
}

// ── Onboarding domain ──

export type OnboardingState = {
  onboarding: OnboardingStatus | null
  onboardingLifecycle: "needs_setup" | "ready"
  setupPercent: number
  preflight: PreflightReport | null
  sourcePacks: SourcePack[]
  previewResult: PreviewResult | null
  previewLoading: boolean
  activateLoading: boolean
  activeSourcePackId: string
  onRunPreflight: () => void
  onApplySourcePack: (packId: string) => void
  onRunPreview: () => void
  onActivate: () => void
}

// ── Timeline domain ──

export type TimelineState = {
  timelineRunId: string
  setTimelineRunId: (value: string) => void
  timelineRuns: TimelineRun[]
  timelineStageFilter: string
  setTimelineStageFilter: (value: string) => void
  timelineStageOptions: string[]
  timelineSeverityFilter: string
  setTimelineSeverityFilter: (value: string) => void
  timelineOrder: "asc" | "desc"
  setTimelineOrder: (value: "asc" | "desc") => void
  timelineLivePaused: boolean
  setTimelineLivePaused: (value: boolean) => void
  timelineSummary: TimelineSummary | null
  timelineRunItems: RunItem[]
  timelineRunArtifacts: RunArtifact[]
  timelineEvents: TimelineEvent[]
  timelineSelectedEventId: number
  setTimelineSelectedEventId: (value: number) => void
  selectedTimelineEvent: TimelineEvent | null
  timelineNoteAuthor: string
  setTimelineNoteAuthor: (value: string) => void
  timelineNoteText: string
  setTimelineNoteText: (value: string) => void
  onRefreshTimeline: () => void
  onExportTimeline: () => void
  onAddTimelineNote: () => void
  timelineNotes: TimelineNote[]
  onSubmitItemFeedback: (itemId: string, label: "more_like_this" | "not_relevant" | "too_technical" | "repeat_source") => void
}

// ── History domain ──

export type HistoryState = {
  history: HistoryItem[]
  activeRollbackId: string
  onRollback: (snapshotId: string) => void
}

// ── Navigation ──

export type NavActions = {
  navigateToSurface: (surface: ConsoleSurface) => void
  onRevisitSetupGuide: () => void
}

// ── Full context ──

export type ConsoleContextValue = {
  ui: UiState
  run: RunState
  source: SourceState
  profile: ProfileState
  schedule: ScheduleState
  onboarding: OnboardingState
  timeline: TimelineState
  historyState: HistoryState
  nav: NavActions
}

const ConsoleContext = createContext<ConsoleContextValue | null>(null)

export function ConsoleProvider({
  value,
  children,
}: {
  value: ConsoleContextValue
  children: ReactNode
}) {
  return <ConsoleContext.Provider value={value}>{children}</ConsoleContext.Provider>
}

function useConsoleContext(): ConsoleContextValue {
  const ctx = useContext(ConsoleContext)
  if (!ctx) throw new Error("useConsoleContext must be used within ConsoleProvider")
  return ctx
}

export function useUiState(): UiState {
  return useConsoleContext().ui
}

export function useRunState(): RunState {
  return useConsoleContext().run
}

export function useSourceState(): SourceState {
  return useConsoleContext().source
}

export function useProfileState(): ProfileState {
  return useConsoleContext().profile
}

export function useScheduleState(): ScheduleState {
  return useConsoleContext().schedule
}

export function useOnboardingState(): OnboardingState {
  return useConsoleContext().onboarding
}

export function useTimelineState(): TimelineState {
  return useConsoleContext().timeline
}

export function useHistoryState(): HistoryState {
  return useConsoleContext().historyState
}

export function useNavActions(): NavActions {
  return useConsoleContext().nav
}
