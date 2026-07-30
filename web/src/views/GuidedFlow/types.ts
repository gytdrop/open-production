// Open Production - Guided Flow v2
// Shared types across shell + stages + data modules.

export type ConfirmGateType = "soft" | "hard"

export type CrewStatus = "ready" | "thinking" | "proposing" | "reviewing" | "idle"

export interface CrewMember {
  id: string
  name: string
  role: string
  defaultStatus: CrewStatus
}

export interface FlowStage {
  num: number
  slug: string
  name: string
  subtitle: string
  leadId: string
  supportingIds: string[]
  reviewerFocus: string
  gate: ConfirmGateType
  accentVar: string
}

export type RightRailTab = "tip" | "glossary" | "audit"

export interface GlossaryTerm {
  term: string
  definition: string
}

export interface AuditEntry {
  id: string
  ts?: string
  actor: string
  action_type: string
  reason?: string
}
