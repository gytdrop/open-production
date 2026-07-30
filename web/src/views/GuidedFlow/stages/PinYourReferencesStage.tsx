import { useProductionStore } from "../../../store/productionStore"
import type { CSSProperties } from "react"

export default function PinYourReferencesStage() {
  const runResult   = useProductionStore((s) => s.runResult)
  const intent      = useProductionStore((s) => s.intent)
  const setFlowStep = useProductionStore((s) => s.setFlowStep)
  const research    = runResult?.research_result
  const refCluster  = runResult?.ref_cluster_result
  const hasCluster  = (refCluster?.proposals ?? []).length > 0

  return (
    <div style={{ animation: "fade-in 0.25s ease" }}>
      <SectionHeader accentVar="--cyan">Pin Your References</SectionHeader>
      <Subtitle>
        Drop references that anchor the tone. Each one gets a SHA-256 hash so nothing is ever lost.
      </Subtitle>

      <h3 style={blockHeading}>Reference tiles</h3>
      <div style={tilesRow}>
        <AddTile kind="image" />
        <AddTile kind="video" />
        <AddTile kind="audio" />
        <AddTile kind="url" />
        {(refCluster?.proposals ?? []).slice(0, 4).map((p, i) => (
          <ReferenceTile key={(p as { id?: string })?.id ?? i} index={i} />
        ))}
      </div>

      <h3 style={blockHeading}>Found while you worked</h3>
      <div style={foundBox}>
        {research ? (
          <>
            <FoundRow label="Source count" value={String(research.source_count)} />
            <FoundRow label="Evidence gate" value={research.gate_passed ? "passed" : "failed"} />
            <FoundRow label="Verdict" value={research.verdict} />
            <p style={{ fontSize: 11, color: "var(--muted)", marginTop: 8, lineHeight: 1.6 }}>
              ResearchAgent scanned for prior work on: <em>{intent.topic || "(no topic)"}</em>. Findings are committed to the audit trail.
            </p>
          </>
        ) : (
          <p style={{ fontSize: 11, color: "var(--dim)", fontStyle: "italic" }}>
            Research findings will appear here once the pipeline has run. Press the Find Your Angle button below to populate this.
          </p>
        )}
      </div>

      <div style={advanceBar}>
        <p style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.5, flex: 1 }}>
          {hasCluster
            ? "Reference clusters are ready. Continue to pick an angle."
            : "No references yet. Skipping is OK - the pipeline can pick the angle from your intent alone."}
        </p>
        <button
          type="button"
          onClick={() => setFlowStep(3)}
          style={advanceBtnStyle}
        >
          Continue to Find Your Angle {"\u2192"}
        </button>
      </div>
    </div>
  )
}

function SectionHeader({ children, accentVar }: { children: React.ReactNode; accentVar: string }) {
  return (
    <h1
      style={{
        fontSize: 26,
        fontWeight: 700,
        color: "var(" + accentVar + ")",
        marginBottom: 6,
        letterSpacing: "-0.02em",
        lineHeight: 1.25,
      }}
    >
      {children}
    </h1>
  )
}

function Subtitle({ children }: { children: React.ReactNode }) {
  return <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 28 }}>{children}</p>
}

const blockHeading: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--purple)",
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  marginBottom: 10,
}

const tilesRow: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
  gap: 10,
  marginBottom: 28,
}

const foundBox: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: 18,
  marginBottom: 28,
}

const advanceBar: CSSProperties = {
  display: "flex",
  gap: 14,
  alignItems: "center",
  padding: 16,
  background: "var(--surface-2)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  marginTop: 8,
}

const advanceBtnStyle: CSSProperties = {
  padding: "10px 18px",
  fontSize: 12,
  fontWeight: 700,
  background: "linear-gradient(135deg, var(--accent) 0%, #4a6ee0 100%)",
  color: "#fff",
  border: "none",
  borderRadius: "var(--radius-md)",
  boxShadow: "0 2px 12px rgba(91,127,255,0.35)",
  cursor: "pointer",
  fontFamily: "inherit",
  whiteSpace: "nowrap",
}

function AddTile({ kind }: { kind: string }) {
  return (
    <button
      title={"Add " + kind}
      aria-label={"Add " + kind}
      style={{
        aspectRatio: "1",
        background: "rgba(255,255,255,0.025)",
        border: "1.5px dashed var(--border2)",
        borderRadius: "var(--radius-md)",
        color: "var(--muted)",
        cursor: "pointer",
        fontFamily: "inherit",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
      }}
    >
      <span style={{ fontSize: 22, opacity: 0.5 }}>+</span>
      <span style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em" }}>{kind}</span>
    </button>
  )
}

function ReferenceTile({ index }: { index: number }) {
  return (
    <div
      style={{
        aspectRatio: "1",
        background: "var(--surface-2)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
        padding: 8,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        cursor: "pointer",
      }}
      title={"ref_" + index.toString().padStart(2, "0")}
    >
      <div style={{ background: "rgba(255,255,255,0.04)", height: 24, borderRadius: 3 }} />
      <span style={{ fontSize: 9, color: "var(--muted)", fontFamily: "monospace" }}>
        ref_{index.toString().padStart(2, "0")}
      </span>
    </div>
  )
}

function FoundRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: 12 }}>
      <span style={{ color: "var(--muted)" }}>{label}</span>
      <span style={{ color: "var(--text)", fontWeight: 600, fontFamily: "monospace" }}>{value}</span>
    </div>
  )
}
