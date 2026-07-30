import type { CSSProperties } from "react"

interface Manifest {
  id: string
  label: string
  duration: string
  aspect: string
  audience: string
  selected: boolean
}

const MANIFESTS: Manifest[] = [
  { id: "tiktok",   label: "TikTok cut",   duration: "02:00", aspect: "9:16", audience: "creators",  selected: false },
  { id: "youtube",  label: "YouTube cut",  duration: "02:00", aspect: "16:9", audience: "film fans", selected: true  },
  { id: "both",     label: "Both + cite",  duration: "02:00", aspect: "9:16 + 16:9 + DOI", audience: "educators", selected: false },
]

const GATES = [
  { name: "Evidence gate",    passed: true,  detail: "All claims sourced." },
  { name: "Consistency gate", passed: true,  detail: "Visual contract honored." },
  { name: "Publication gate", passed: true,  detail: "Ready for distribution." },
]

export default function PublishWithEvidenceStage() {
  return (
    <div style={{ animation: "fade-in 0.25s ease" }}>
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--pink)",
          marginBottom: 6,
          letterSpacing: "-0.02em",
        }}
      >
        Publish with Evidence
      </h1>
      <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 24 }}>
        Ready to publish. Three manifest proposals - pick one.
      </p>

      <h3 style={blockHeading}>Manifests</h3>
      <div style={manifestsGrid}>
        {MANIFESTS.map((m) => (
          <ManifestCard key={m.id} manifest={m} />
        ))}
      </div>

      <h3 style={{ ...blockHeading, marginTop: 8 }}>Final gate</h3>
      <div style={gateBox}>
        {GATES.map((g) => (
          <GateRow key={g.name} name={g.name} passed={g.passed} detail={g.detail} />
        ))}
      </div>

      <h3 style={{ ...blockHeading, marginTop: 8 }}>Audit summary</h3>
      <div style={summaryBox}>
        <SummaryRow label="Agents ran"        value="21" />
        <SummaryRow label="Decisions logged"  value="47" />
        <SummaryRow label="Gates passed"      value="3 of 3" />
        <SummaryRow label="Contradictions"    value="0" />
        <a
          href="#"
          onClick={(e) => e.preventDefault()}
          style={{
            display: "inline-block",
            marginTop: 10,
            fontSize: 11,
            color: "var(--accent)",
            textDecoration: "underline",
          }}
        >
          View full audit trail -&gt;
        </a>
      </div>

      <button style={publishBtnStyle}>Confirm and Publish -&gt;</button>
    </div>
  )
}

const blockHeading: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--pink)",
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  marginBottom: 10,
}

const manifestsGrid: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
  gap: 12,
  marginBottom: 24,
}

function ManifestCard({ manifest }: { manifest: Manifest }) {
  return (
    <article
      style={{
        background: "var(--surface-1)",
        border: "1px solid " + (manifest.selected ? "var(--pink)" : "var(--border)"),
        borderRadius: "var(--radius-md)",
        padding: 14,
        boxShadow: manifest.selected ? "0 0 0 2px var(--pink)33" : "none",
      }}
    >
      <h4 style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", marginBottom: 6 }}>
        {manifest.label}
      </h4>
      <p style={{ fontSize: 11, color: "var(--muted)", fontFamily: "monospace" }}>
        {manifest.duration} / {manifest.aspect}
      </p>
      <p style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
        audience: <span style={{ color: "var(--text2)" }}>{manifest.audience}</span>
      </p>
      <div style={{ display: "flex", gap: 6, marginTop: 10 }}>
        <Pill color="var(--green)" label="review: ok" />
        <Pill color="var(--green)" label="gate: ok" />
      </div>
      <button style={publishCardBtnStyle(manifest.selected)}>
        {manifest.selected ? "Selected" : "Publish"}
      </button>
    </article>
  )
}

function Pill({ color, label }: { color: string; label: string }) {
  return (
    <span
      style={{
        fontSize: 9,
        fontWeight: 700,
        color,
        background: color + "22",
        padding: "2px 8px",
        borderRadius: 20,
        textTransform: "uppercase",
        letterSpacing: "0.04em",
      }}
    >
      {label}
    </span>
  )
}

const gateBox: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: 14,
  marginBottom: 20,
}

function GateRow({ name, passed, detail }: { name: string; passed: boolean; detail: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "6px 0",
        fontSize: 12,
      }}
    >
      <span
        aria-hidden
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: 18,
          height: 18,
          borderRadius: "50%",
          background: passed ? "rgba(45,206,122,0.18)" : "rgba(245,166,35,0.18)",
          color: passed ? "var(--green)" : "var(--amber)",
          fontWeight: 700,
          fontSize: 11,
        }}
      >
        {passed ? "✓" : "!"}
      </span>
      <span style={{ color: "var(--text)", fontWeight: 600 }}>{name}</span>
      <span style={{ color: "var(--muted)" }}>- {detail}</span>
    </div>
  )
}

const summaryBox: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: 14,
  marginBottom: 24,
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: 12 }}>
      <span style={{ color: "var(--muted)" }}>{label}</span>
      <span style={{ color: "var(--text)", fontWeight: 600, fontFamily: "monospace" }}>{value}</span>
    </div>
  )
}

function publishCardBtnStyle(selected: boolean): CSSProperties {
  return {
    marginTop: 12,
    width: "100%",
    padding: "8px 0",
    background: selected ? "var(--pink)" : "transparent",
    color: selected ? "#fff" : "var(--pink)",
    border: "1px solid var(--pink)",
    borderRadius: "var(--radius-md)",
    fontSize: 11,
    fontWeight: 700,
    cursor: "pointer",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    fontFamily: "inherit",
  }
}

const publishBtnStyle: CSSProperties = {
  width: "100%",
  padding: "14px 20px",
  background: "linear-gradient(135deg, var(--pink) 0%, #d04878 100%)",
  color: "#fff",
  border: "none",
  borderRadius: "var(--radius-md)",
  fontSize: 13,
  fontWeight: 700,
  cursor: "pointer",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
  boxShadow: "0 2px 12px rgba(240,98,146,0.35)",
  fontFamily: "inherit",
}
