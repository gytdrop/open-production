import { useState } from "react"
import type { AuditEntry, CrewMember, FlowStage, RightRailTab } from "../types"
import { GLOSSARY } from "../data/glossary"

interface Props {
  stage: FlowStage
  selectedAgent: CrewMember | null
  onCloseAgent: () => void
  auditEntries: AuditEntry[]
}

export default function RightRail({ stage, selectedAgent, onCloseAgent, auditEntries }: Props) {
  const [tab, setTab] = useState<RightRailTab>("tip")
  const effectiveTab: RightRailTab = selectedAgent ? "tip" : tab
  const locked = !!selectedAgent

  return (
    <aside
      aria-label="Stage help and details"
      style={{
        width: 300,
        flexShrink: 0,
        background: "var(--bg2)",
        borderLeft: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Tabs current={effectiveTab} onChange={setTab} disabled={locked} />
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px" }}>
        {selectedAgent ? (
          <AgentDetail agent={selectedAgent} onClose={onCloseAgent} />
        ) : effectiveTab === "tip" ? (
          <TipPanel stage={stage} />
        ) : effectiveTab === "glossary" ? (
          <GlossaryPanel stageNum={stage.num} />
        ) : (
          <AuditPanel entries={auditEntries} />
        )}
      </div>
    </aside>
  )
}

function Tabs({ current, onChange, disabled }: { current: RightRailTab; onChange: (t: RightRailTab) => void; disabled?: boolean }) {
  const tabs: Array<{ id: RightRailTab; label: string }> = [
    { id: "tip", label: "Tip" },
    { id: "glossary", label: "Glossary" },
    { id: "audit", label: "Audit" },
  ]
  return (
    <div role="tablist" style={{ display: "flex", borderBottom: "1px solid var(--border)" }}>
      {tabs.map((t) => {
        const active = current === t.id
        return (
          <button
            key={t.id}
            role="tab"
            aria-selected={active}
            disabled={disabled}
            onClick={() => onChange(t.id)}
            style={{
              flex: 1,
              padding: "10px 0",
              background: "transparent",
              border: "none",
              borderBottom: active ? "2px solid var(--accent)" : "2px solid transparent",
              color: active ? "var(--text)" : disabled ? "var(--dim)" : "var(--muted)",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: disabled ? 0.5 : 1,
              transition: "color 0.15s, border-color 0.15s",
              fontFamily: "inherit",
            }}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}

function TipPanel({ stage }: { stage: FlowStage }) {
  return (
    <div>
      <SectionHeader color="var(--purple)">Studio Tip</SectionHeader>
      <TipBody>{tipForStage(stage.num)}</TipBody>
      <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "14px 0" }} />
      <SectionHeader color="var(--cyan)">Why this?</SectionHeader>
      <TipBody muted>{whyForStage(stage.num)}</TipBody>
    </div>
  )
}

function GlossaryPanel({ stageNum }: { stageNum: number }) {
  const terms = GLOSSARY[stageNum] ?? []
  return (
    <div>
      <SectionHeader color="var(--accent)">Glossary</SectionHeader>
      {terms.length === 0 ? (
        <TipBody muted>(no terms for this stage yet)</TipBody>
      ) : (
        terms.map((t) => (
          <div key={t.term} style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text)" }}>{t.term}</div>
            <div style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.6 }}>{t.definition}</div>
          </div>
        ))
      )}
    </div>
  )
}

function AuditPanel({ entries }: { entries: AuditEntry[] }) {
  return (
    <div>
      <SectionHeader color="var(--amber)">Audit Trail</SectionHeader>
      {entries.length === 0 ? (
        <TipBody muted>No decisions logged yet for this stage.</TipBody>
      ) : (
        entries.slice(-10).map((e, i) => (
          <div
            key={i}
            style={{
              padding: "8px 10px",
              marginBottom: 6,
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              fontSize: 11,
            }}
          >
            <div style={{ fontWeight: 700, color: "var(--text)" }}>{e.action_type}</div>
            {e.reason && <div style={{ color: "var(--muted)", marginTop: 2 }}>{e.reason}</div>}
          </div>
        ))
      )}
    </div>
  )
}

function AgentDetail({ agent, onClose }: { agent: CrewMember; onClose: () => void }) {
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <SectionHeader color="var(--purple)">Agent Detail</SectionHeader>
        <button
          onClick={onClose}
          aria-label="Close detail"
          style={{
            background: "transparent",
            border: "none",
            color: "var(--muted)",
            fontSize: 14,
            cursor: "pointer",
            padding: 4,
            fontFamily: "inherit",
          }}
        >
          {"✕"}
        </button>
      </div>
      <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>{agent.name}</div>
      <div style={{ fontSize: 11, color: "var(--accent)", fontFamily: "monospace", marginTop: 2 }}>
        {agent.id}.py
      </div>
      <div style={{ fontSize: 12, color: "var(--text2)", marginTop: 12, lineHeight: 1.6 }}>
        {agent.role}
      </div>
    </div>
  )
}

function SectionHeader({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <div
      style={{
        fontSize: 10,
        fontWeight: 800,
        color,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  )
}

function TipBody({ children, muted }: { children: React.ReactNode; muted?: boolean }) {
  return (
    <div style={{ fontSize: 12, color: muted ? "var(--muted)" : "var(--text2)", lineHeight: 1.65 }}>
      {children}
    </div>
  )
}

function tipForStage(n: number): string {
  switch (n) {
    case 1: return "A few sentences is fine. You can change anything later - the production document keeps every version."
    case 2: return "Each reference gets a SHA-256 hash so nothing is ever lost. Drop images, video clips, audio, or URLs."
    case 3: return "The Reviewer has already scored each angle for fit with your brief. Hover any angle to see the score."
    case 4: return "Every character gets a consistency contract - visual anchors the Reviewer uses to check every generated frame."
    case 5: return "The storyboard is ASCII for now - fine for planning. Real frames render in Stage 6."
    case 6: return "Every pass is gated by the Reviewer. Skipping is fine; skipping-and-failing is not."
    case 7: return "Your audit trail travels with the production. Anyone receiving it can replay the entire process."
    default: return "You can change anything later."
  }
}

function whyForStage(n: number): string {
  switch (n) {
    case 1: return "ResearchAgent is already scanning for prior work on this topic. Findings will appear in Stage 2."
    case 2: return "ReferenceClusteringAgent groups references by visual and tonal cluster, then extracts style tokens."
    case 3: return "CreativeReframing produces 3 angles by sampling tone, pace, and fit from your references."
    case 4: return "CharacterDirector proposes from your tone and references; EnvironmentArtist locks lighting per location."
    case 5: return "ShotPlanning picks framings to maximize the chosen angle. Edit any field inline."
    case 6: return "GenerationAgent runs the backend; EditorAgent assembles the timeline. Reviewer checks every artifact."
    case 7: return "PublisherAgent proposes 3 manifest targets. PublicationGate is the final fail-closed check."
    default: return ""
  }
}
