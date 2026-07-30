import { useState, type CSSProperties } from "react"

type PassStatus = "approved" | "running" | "queued" | "flagged"

interface Pass {
  id: string
  label: string
  status: PassStatus
  agent: string
  detail: string
}

const INITIAL: Pass[] = [
  { id: "frames",   label: "Frames",       status: "approved", agent: "GenerationAgent",      detail: "5 shots rendered. All pass consistency gate." },
  { id: "voice",    label: "Voice + Music", status: "running",  agent: "VoiceDirector + MusicComposer", detail: "Voice 72%, Music 31%." },
  { id: "sound",    label: "Sound",         status: "queued",   agent: "SoundDesigner",       detail: "" },
  { id: "color",    label: "Color",         status: "queued",   agent: "Colorist",            detail: "" },
  { id: "edit",     label: "Edit",          status: "queued",   agent: "Editor",              detail: "" },
  { id: "reviewer", label: "Reviewer",      status: "queued",   agent: "ReviewerAgent",       detail: "" },
]

export default function GenerateAndPolishStage() {
  const [passes, setPasses] = useState<Pass[]>(INITIAL)

  function approve(p: Pass) {
    setPasses((cur) => cur.map((x) => (x.id === p.id ? { ...x, status: "approved" } : x)))
  }
  function skipNext() {
    setPasses((cur) => {
      const idx = cur.findIndex((x) => x.status === "running" || x.status === "queued")
      if (idx === -1) return cur
      return cur.map((x, i) => {
        if (i === idx) return { ...x, status: "approved" }
        if (i === idx + 1) return { ...x, status: "running" }
        return x
      })
    })
  }

  const doneCount = passes.filter((p) => p.status === "approved").length

  return (
    <div style={{ animation: "fade-in 0.25s ease" }}>
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--amber)",
          marginBottom: 6,
          letterSpacing: "-0.02em",
        }}
      >
        Generate and Polish
      </h1>
      <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 24 }}>
        The crew is working. Approve each pass. Override any frame.
      </p>

      <div style={progressBar}>
        <div style={{ ...progressFill, width: (doneCount / passes.length) * 100 + "%" }} />
      </div>
      <p style={{ fontSize: 11, color: "var(--dim)", marginBottom: 18 }}>
        {doneCount} of {passes.length} passes approved
      </p>

      {passes.map((p) => (
        <PassCard key={p.id} pass={p} onApprove={() => approve(p)} />
      ))}

      <button onClick={skipNext} style={skipBtnStyle}>
        Skip to next pass (power user)
      </button>
    </div>
  )
}

const progressBar: CSSProperties = {
  height: 2,
  background: "var(--border)",
  borderRadius: 1,
  overflow: "hidden",
  marginBottom: 6,
}

const progressFill: CSSProperties = {
  height: "100%",
  background: "linear-gradient(90deg, var(--accent) 0%, var(--purple) 100%)",
  transition: "width 0.5s ease",
}

function PassCard({ pass, onApprove }: { pass: Pass; onApprove: () => void }) {
  return (
    <article style={passCard(pass.status)}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <p style={passLabel(pass.status)}>
            {pass.label}
            <span style={{ marginLeft: 10, fontSize: 10, color: "var(--dim)", fontFamily: "monospace", textTransform: "none" }}>
              {pass.agent}
            </span>
          </p>
          {pass.detail && <p style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>{pass.detail}</p>}
        </div>
        <StatusBadge status={pass.status} />
      </div>
      {(pass.status === "running" || pass.status === "queued") && (
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button onClick={onApprove} style={actionBtnStyle("approve")}>Approve</button>
          <button style={actionBtnStyle("override")}>Override</button>
          <button style={actionBtnStyle("rerun")}>Re-run</button>
        </div>
      )}
    </article>
  )
}

function StatusBadge({ status }: { status: PassStatus }) {
  const map: Record<PassStatus, { label: string; color: string; bg: string }> = {
    approved: { label: "approved", color: "var(--green)",  bg: "rgba(45,206,122,0.12)" },
    running:  { label: "running",  color: "var(--amber)",  bg: "rgba(245,166,35,0.12)" },
    queued:   { label: "queued",   color: "var(--muted)",  bg: "rgba(255,255,255,0.04)" },
    flagged:  { label: "flagged",  color: "var(--pink)",   bg: "rgba(240,98,146,0.12)" },
  }
  const m = map[status]
  return (
    <span
      style={{
        fontSize: 10,
        fontWeight: 700,
        color: m.color,
        background: m.bg,
        padding: "3px 10px",
        borderRadius: 20,
        letterSpacing: "0.05em",
        textTransform: "uppercase",
      }}
    >
      {m.label}
    </span>
  )
}

function passCard(status: PassStatus): CSSProperties {
  return {
    background: "var(--surface-1)",
    border: "1px solid " + (status === "running" ? "var(--amber)" : "var(--border)"),
    borderLeft: "3px solid " + accentForStatus(status),
    borderRadius: "var(--radius-md)",
    padding: 14,
    marginBottom: 10,
  }
}

function accentForStatus(status: PassStatus): string {
  if (status === "approved") return "var(--green)"
  if (status === "running")  return "var(--amber)"
  if (status === "flagged")  return "var(--pink)"
  return "var(--border2)"
}

function passLabel(status: PassStatus): CSSProperties {
  return {
    fontSize: 13,
    fontWeight: 700,
    color: status === "queued" ? "var(--dim)" : "var(--text)",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  }
}

function actionBtnStyle(kind: "approve" | "override" | "rerun"): CSSProperties {
  const colors: Record<typeof kind, string> = {
    approve: "var(--green)",
    override: "var(--purple)",
    rerun: "var(--amber)",
  }
  const c = colors[kind]
  return {
    padding: "5px 12px",
    background: "transparent",
    border: "1px solid " + c,
    borderRadius: "var(--radius-sm)",
    fontSize: 11,
    fontWeight: 700,
    color: c,
    cursor: "pointer",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    fontFamily: "inherit",
  }
}

const skipBtnStyle: CSSProperties = {
  marginTop: 8,
  padding: "8px 14px",
  background: "transparent",
  border: "1px dashed var(--border2)",
  borderRadius: "var(--radius-md)",
  color: "var(--muted)",
  fontSize: 11,
  cursor: "pointer",
  fontFamily: "inherit",
}
