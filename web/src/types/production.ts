// TypeScript mirror of src/schema/production_document.py.
//
// UI-FACING SUBSET: this file intentionally mirrors only the fields
// the React UI consumes. The Python schema is the source of truth and
// includes additional fields not yet surfaced (e.g. Character.visual_anchors,
// Character.consistency_contract, Environment.lighting_presets, Shot.characters,
// Studio, Timeline). Do not try to keep them in sync one-for-one; instead,
// add a field here only when the UI actually needs it.
//
// If a Python field is added and the UI needs it, add the corresponding
// field here AND add a test or a runtime guard that surfaces the missing
// data in a visible way.

// ── Literal unions ─────────────────────────────────────────────────────────

export type ProductionState =
  | 'DRAFT'
  | 'BRIEFED'
  | 'IN_PRODUCTION'
  | 'IN_REVIEW'
  | 'APPROVED'
  | 'PUBLISHED'

export type ActionType =
  | 'gate_decision'
  | 'decision'
  | 'lock'
  | 'unlock'
  | 'snapshot'
  | 'branch'
  | 'merge'
  | 'state_transition'
  | 'stage_advance'
  | 'override'
  | 'comment'
  | 'system'

export type ShotStatus =
  | 'draft'
  | 'in_production'
  | 'generated'
  | 'in_review'
  | 'approved'
  | 'rejected'

export type ReferenceKind = 'image' | 'video' | 'audio' | 'text' | 'url'

export type CameraMovement =
  | 'static'
  | 'pan'
  | 'tilt'
  | 'dolly'
  | 'push_in'
  | 'pull_out'
  | 'handheld'
  | 'custom'

export type CameraFraming =
  | 'extreme_close'
  | 'close'
  | 'medium'
  | 'wide'
  | 'extreme_wide'
  | 'over_the_shoulder'
  | 'custom'

// ── Core dataclasses ───────────────────────────────────────────────────────

export interface IntentDocument {
  topic: string
  audience?: string
  tone?: string
  platform?: string
  duration_sec?: number
  style_seed?: string
  extra?: Record<string, unknown>
}

export interface Reference {
  id: string
  kind: ReferenceKind
  label: string
  uri?: string
  sha256?: string
  pinned_by?: string
  pinned_at?: string
}

export interface CameraSpec {
  focal_length_mm?: number
  frame_rate?: number
  aperture?: string
  movement?: CameraMovement
  framing?: CameraFraming
  preset_id?: string
}

export interface LightingSpec {
  key_intensity_pct?: number
  fill_intensity_pct?: number
  color_temp_k?: number
  preset_id?: string
}

export interface AudioSpec {
  voice_direction?: string
  sfx?: string[]
  music_cue?: string
}

export interface Shot {
  id: string
  scene_id: string
  intent: string
  duration_sec: number
  status: ShotStatus
  camera?: CameraSpec
  lighting?: LightingSpec
  audio?: AudioSpec
  locked: boolean
  storyboard_frame?: string
  color_spec?: Record<string, unknown>
  motion_spec?: Record<string, unknown>
}

export interface Scene {
  id: string
  name: string
  shots: Shot[]
  location?: string
  notes?: string
  stage?: string
}

export interface AuditEntry {
  id: string
  ts: string
  actor: string
  action_type: ActionType
  gate_name?: string
  claim_id?: string
  decision_status?: string
  reason?: string
  evidence: Record<string, unknown>
  payload: Record<string, unknown>
  state_before?: string
  state_after?: string
}

export interface Branch {
  id: string
  name: string
  created_at: string
  parent_snapshot_id?: string
  created_by?: string
  locked: boolean
}

export interface VersionSnapshot {
  id: string
  taken_at: string
  content_hash: string
  taken_by?: string
  label?: string
  branch_id?: string
}

export interface Character {
  id: string
  name: string
  role?: string
  voice_id?: string
}

export interface Environment {
  id: string
  name: string
  time_of_day_variants?: string[]
}

export interface Production {
  id: string
  state: ProductionState
  intent: IntentDocument
  scenes: Scene[]
  audit_trail: AuditEntry[]
  title?: string
  created_at: string
  updated_at: string
  references: Reference[]
  characters: Character[]
  environments: Environment[]
  branches: Branch[]
  snapshots: VersionSnapshot[]
  metadata: Record<string, unknown>
}

// ── API response shapes ────────────────────────────────────────────────────

export interface Angle {
  id: string
  name: string
  summary: string
  risk_focus: string
  questions_to_address: string[]
}

export interface DemoRunResult {
  topic: string
  audience: string
  tone: string
  angles: Angle[]
  chosen_angle: Angle
  accepted_claims: number
  rejected_claims: number
  contradictions: unknown[]
  summary: string
  audit_path: string
  audit_entries: AuditEntry[]
  production_id: string | null
  reviewer_results: unknown[]
  research_result: { gate_passed: boolean; source_count: number; verdict: string }
  ref_cluster_result?: { proposals?: unknown[] }
  moodboard_result?: { proposals?: unknown[] }
  env_result: { proposals?: unknown[] }
  shot_plan_result: { shots?: unknown[] }
  editor_result: { proposals?: unknown[] }
  branch_result: { branch_id?: string; snapshot_id?: string }
  publish_result: { proposals?: unknown[] }
  archive_result: { archived_at?: string; expires_at?: string }
}
