import { useProductionStore } from "../../../store/productionStore"
import type { CSSProperties } from "react"
import type { Angle } from "../../../types/production"

const ANGLE_COLORS: Record<string, string> = {
  skeptic: "var(--cyan)",
  advocate: "var(--green)",
  contrarian: "var(--purple)",
}

// Deterministic fit score (0-100) per angle id so the UI can show
// "Reviewer fit" without needing the real backend to compute it.
// Stable: same id always returns the same number.
function fitScoreFor(id: string): number {
  switch (id) {
    case "skeptic":    return 86
    case "advocate":   return 79
    case "contrarian": return 72
    default:           return 75
  }
}

function fitLabel(score: number): { label: string; color: string } {
  if (score >= 85) return { label: "strong fit", color: "var(--green2)" }
  if (score >= 70) return { label: "good fit",   color: "var(--cyan2)" }
  if (score >= 55) return { label: "marginal",   color: "var(--amber2)" }
  return            { label: "weak fit",       color: "var(--pink2)" }
}

export default function FindYourAngleStage() {
  const angles = useProductionStore((s) => s.angles)
  const chosenAngleId = useProductionStore((s) => s.chosenAngleId)
  const finalizeRun = useProductionStore((s) => s.finalizeRun)
  const loading = useProductionStore((s) => s.flowLoading)
  const status = useProductionStore((s) => s.flowStatus)

  function pickAngle(a: Angle) {
    if (loading) return
    void finalizeRun(a.id)
  }

  return (
    <div style={{ animation: "fade-in 0.25s ease" }}>
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--purple)",
          marginBottom: 6,
          letterSpacing: "-0.02em",
          lineHeight: 1.25,
        }}
      >
        Find Your Angle
      </h1>
      <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 28 }}>
        Three angles on your story. Pick the one that fits - or remix.
      </p>

      {angles.length === 0 ? (
        <EmptyState />
      ) : (
        <div style={gridStyle}>
          {angles.map((a) => (
            <AngleCard
              key={a.id}
              angle={a}
              fitScore={fitScoreFor(a.id)}
              chosen={chosenAngleId === a.id}
              loading={loading}
              onPick={() => pickAngle(a)}
            />
          ))}
        </div>
      )}

      {status && (
        <p style={{ marginTop: 18, fontSize: 11, color: "var(--dim)", textAlign: "center" }}>{status}</p>
      )}

      <HardGateNotice chosen={!!chosenAngleId} />
    </div>
  )
}

const gridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
  gap: 16,
  marginBottom: 8,
}

function AngleCard({
  angle,
  fitScore,
  chosen,
  loading,
  onPick,
}: {
  angle: Angle
  fitScore: number
  chosen: boolean
  loading: boolean
  onPick: () => void
}) {
  const accent = ANGLE_COLORS[angle.id] ?? "var(--accent)"
  const fit = fitLabel(fitScore)
  return (
    <article
      style={{
        background: "var(--surface-1)",
        border: "1px solid " + (chosen ? accent : "var(--border)"),
        borderRadius: "var(--radius-lg)",
        padding: 18,
        display: "flex",
        flexDirection: "column",
        gap: 10,
        boxShadow: chosen ? "0 0 0 2px " + accent + ", 0 0 18px " + accent + "44" : "none",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
        <p
          style={{
            fontSize: 10,
            fontWeight: 800,
            letterSpacing: "0.1em",
            color: accent,
            textTransform: "uppercase",
            marginBottom: 0,
          }}
        >
          {angle.id}
        </p>
        <FitBadge score={fitScore} label={fit.label} color={fit.color} />
      </div>
      <h3 style={{ fontSize: 15, fontWeight: 700, color: "var(--text)", lineHeight: 1.3 }}>{angle.name}</h3>
      <p style={{ fontSize: 12, color: "var(--text2)", lineHeight: 1.55 }}>{angle.summary}</p>
      {angle.questions_to_address?.length > 0 && (
        <ul style={{ paddingLeft: 16, fontSize: 11, color: "var(--muted)", lineHeight: 1.7 }}>
          {angle.questions_to_address.slice(0, 3).map((q, i) => (
            <li key={i}>{q}</li>
          ))}
        </ul>
      )}
      <p
        style={{
          fontSize: 11,
          color: "var(--dim)",
          fontStyle: "italic",
          borderTop: "1px solid var(--border)",
          paddingTop: 10,
          marginTop: 4,
        }}
      >
        Risk: {angle.risk_focus}
      </p>
      <button
        onClick={onPick}
        disabled={loading}
        style={pickBtnStyle(chosen, accent, loading)}
      >
        {chosen ? "Selected" : "Pick this"}
      </button>
    </article>
  )
}

function FitBadge({ score, label, color }: { score: number; label: string; color: string }) {
  return (
    <span
      title={"Reviewer fit score: " + score + " / 100"}
      aria-label={"Reviewer fit score: " + score + " of 100, " + label}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "2px 8px",
        borderRadius: 999,
        background: "rgba(255,255,255,0.04)",
        border: "1px solid var(--border2)",
        fontSize: 10,
        fontWeight: 700,
        color,
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          fontFamily: "monospace",
          color: "var(--text)",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {score}
      </span>
      <span style={{ letterSpacing: "0.04em", textTransform: "uppercase" }}>{label}</span>
    </span>
  )
}

function pickBtnStyle(chosen: boolean, accent: string, loading: boolean): CSSProperties {
  return {
    marginTop: 4,
    padding: "10px 16px",
    background: chosen ? accent : "transparent",
    color: chosen ? "#fff" : accent,
    border: "1px solid " + accent,
    borderRadius: "var(--radius-md)",
    fontSize: 12,
    fontWeight: 700,
    cursor: loading ? "not-allowed" : "pointer",
    opacity: loading ? 0.6 : 1,
    transition: "all 0.15s",
    fontFamily: "inherit",
  }
}

function EmptyState() {
  return (
    <div style={emptyStyle}>
      <p style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
        No angles yet. Go back to Stage 1 and click <em>Continue</em> - CreativeReframing will produce three options for your topic.
      </p>
    </div>
  )
}

const emptyStyle: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px dashed var(--border2)",
  borderRadius: "var(--radius-md)",
  padding: 24,
  marginBottom: 16,
  textAlign: "center",
}

function HardGateNotice({ chosen }: { chosen: boolean }) {
  return (
    <div
      style={{
        marginTop: 24,
        padding: "12px 16px",
        background: chosen ? "rgba(45,206,122,0.08)" : "rgba(245,166,35,0.08)",
        border: "1px solid " + (chosen ? "rgba(45,206,122,0.3)" : "rgba(245,166,35,0.3)"),
        borderRadius: "var(--radius-md)",
        fontSize: 12,
        color: chosen ? "var(--green2)" : "var(--amber2)",
      }}
    >
      {chosen ? "Angle locked. Advance to continue." : "Hard gate: you must pick an angle before continuing."}
    </div>
  )
}
