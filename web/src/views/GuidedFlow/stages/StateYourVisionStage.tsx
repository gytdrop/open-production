import { useState, type CSSProperties } from "react"
import { useProductionStore } from "../../../store/productionStore"

const PLATFORMS = ["TikTok", "Instagram", "YouTube", "Other"] as const
const TONES = ["Warm", "Neutral", "Tense", "Hopeful"] as const
const MAX_CHARS = 500
const PLACEHOLDER = "e.g. A short film about a barista who discovers their regular customer is an AI testing whether humans can tell..."

export default function StateYourVisionStage() {
  const setIntent   = useProductionStore((s) => s.setIntent)
  const loadAngles  = useProductionStore((s) => s.loadAngles)
  const flowLoading = useProductionStore((s) => s.flowLoading)
  const flowStatus  = useProductionStore((s) => s.flowStatus)
  const intent      = useProductionStore((s) => s.intent)

  const [platform, setPlatform] = useState<string>("TikTok")
  const [tone, setTone]         = useState<string>(intent.tone || "Neutral")
  const [topic, setTopic]       = useState(intent.topic)
  const [focused, setFocused]   = useState(false)
  const [scriptMode, setScriptMode] = useState(false)

  function handleContinue() {
    if (!topic.trim() || flowLoading) return
    setIntent({ topic: topic.trim(), audience: intent.audience || "", tone })
    void loadAngles()
  }

  const canSubmit = topic.trim().length > 0 && !flowLoading

  return (
    <div style={rootStyle}>
      <Headline />

      {!scriptMode ? (
        <>
          <TopicField
            topic={topic}
            setTopic={setTopic}
            focused={focused}
            setFocused={setFocused}
          />
          <PlatformPicker value={platform} onChange={setPlatform} />
          <TonePicker value={tone} onChange={setTone} />
          <ContinueRow
            canSubmit={canSubmit}
            loading={flowLoading}
            status={flowStatus}
            onClick={handleContinue}
            onScriptAlt={() => setScriptMode(true)}
          />
        </>
      ) : (
        <ScriptPaste
          onCancel={() => setScriptMode(false)}
        />
      )}

      <WhatHappensNext />
    </div>
  )
}

function Headline() {
  return (
    <div style={{ textAlign: "center", marginBottom: 24 }}>
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--text)",
          marginBottom: 6,
          letterSpacing: "-0.02em",
          lineHeight: 1.25,
        }}
      >
        What story do you want to tell?
      </h1>
      <p style={{ fontSize: 13, color: "var(--muted)" }}>
        A few sentences is fine - the pipeline will help you develop it.
      </p>
    </div>
  )
}

interface TopicFieldProps {
  topic: string
  setTopic: (v: string) => void
  focused: boolean
  setFocused: (v: boolean) => void
}

function TopicField({ topic, setTopic, focused, setFocused }: TopicFieldProps) {
  return (
    <div style={{ position: "relative", marginBottom: 28 }}>
      <textarea
        value={topic}
        onChange={(e) => setTopic(e.target.value.slice(0, MAX_CHARS))}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={PLACEHOLDER}
        aria-label="Production topic"
        style={{
          width: "100%",
          minHeight: 140,
          background: focused ? "rgba(255,255,255,0.055)" : "rgba(255,255,255,0.035)",
          border: "1px solid " + (focused ? "var(--accent)" : "var(--border2)"),
          borderRadius: "var(--radius-md)",
          color: "var(--text)",
          fontSize: 13,
          lineHeight: 1.65,
          padding: "14px 16px",
          resize: "vertical",
          transition: "border-color 0.2s, background 0.2s",
          outline: "none",
          fontFamily: "inherit",
        }}
      />
      <span
        style={{
          position: "absolute",
          bottom: 10,
          right: 14,
          fontSize: 10,
          color: topic.length > MAX_CHARS * 0.9 ? "var(--amber)" : "var(--dim)",
          fontVariantNumeric: "tabular-nums",
          pointerEvents: "none",
        }}
      >
        {topic.length}/{MAX_CHARS}
      </span>
    </div>
  )
}

function PlatformPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Picker
      label="Where will it live?"
      options={PLATFORMS}
      value={value}
      onChange={onChange}
      shape="pill"
    />
  )
}

function TonePicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <Picker
      label="What tone?"
      options={TONES}
      value={value}
      onChange={onChange}
      shape="square"
    />
  )
}

interface PickerProps {
  label: string
  options: readonly string[]
  value: string
  onChange: (v: string) => void
  shape: "pill" | "square"
}

function Picker({ label, options, value, onChange, shape }: PickerProps) {
  return (
    <div style={{ marginBottom: 26 }}>
      <p style={pickerLabelStyle}>{label}</p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {options.map((o) => {
          const active = value === o
          const style: CSSProperties = shape === "pill" ? pillStyle(active) : squareStyle(active)
          return (
            <button key={o} type="button" onClick={() => onChange(o)} style={style}>
              {o}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function pillStyle(active: boolean): CSSProperties {
  return {
    borderRadius: 20,
    padding: "8px 22px",
    fontSize: 12,
    fontWeight: active ? 600 : 400,
    background: active ? "rgba(91,127,255,0.18)" : "rgba(255,255,255,0.03)",
    border: "1px solid " + (active ? "var(--accent)" : "var(--border2)"),
    color: active ? "var(--accent2)" : "var(--muted)",
    cursor: "pointer",
    transition: "all 0.15s",
    fontFamily: "inherit",
  }
}

function squareStyle(active: boolean): CSSProperties {
  return {
    borderRadius: "var(--radius-md)",
    padding: "7px 18px",
    fontSize: 12,
    fontWeight: active ? 600 : 400,
    background: active ? "rgba(91,127,255,0.18)" : "rgba(255,255,255,0.03)",
    border: "1px solid " + (active ? "var(--accent)" : "var(--border2)"),
    color: active ? "var(--accent2)" : "var(--muted)",
    cursor: "pointer",
    transition: "all 0.15s",
    fontFamily: "inherit",
  }
}

interface ContinueRowProps {
  canSubmit: boolean
  loading: boolean
  status: string
  onClick: () => void
  onScriptAlt: () => void
}

function ContinueRow({ canSubmit, loading, status, onClick, onScriptAlt }: ContinueRowProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
      <button onClick={onScriptAlt} style={scriptLinkStyle}>
        I have a script - paste it instead
      </button>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {status && !loading && <span style={{ fontSize: 11, color: "var(--dim)" }}>{status}</span>}
        <button onClick={onClick} disabled={!canSubmit} style={continueBtnStyle(canSubmit)}>
          {loading ? "Generating angles..." : "Continue →"}
        </button>
      </div>
    </div>
  )
}

function ScriptPaste({ onCancel }: { onCancel: () => void }) {
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        padding: 22,
        marginBottom: 24,
      }}
    >
      <h3 style={{ fontSize: 14, fontWeight: 700, color: "var(--purple)", marginBottom: 10 }}>
        Paste your script
      </h3>
      <textarea
        placeholder="Paste the full script here. The pipeline will skip Stage 3 (Find Your Angle) and go straight to Story & Script refinement."
        style={{
          width: "100%",
          minHeight: 220,
          background: "var(--bg2)",
          border: "1px solid var(--border2)",
          borderRadius: "var(--radius-md)",
          color: "var(--text)",
          padding: "12px 14px",
          fontSize: 12,
          fontFamily: "monospace",
          lineHeight: 1.5,
          outline: "none",
        }}
      />
      <p style={{ fontSize: 11, color: "var(--muted)", marginTop: 10, lineHeight: 1.6 }}>
        Coming in a later phase: this lets you skip creative reframing when you already have material.
      </p>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 14 }}>
        <button onClick={onCancel} style={cancelBtnStyle}>Back to intent form</button>
      </div>
    </div>
  )
}

function WhatHappensNext() {
  return (
    <div style={whatNextStyle}>
      <div style={{ width: 4, alignSelf: "stretch", background: "var(--purple)", borderRadius: 2, flexShrink: 0, opacity: 0.6 }} />
      <div>
        <p style={whatNextLabelStyle}>What happens next</p>
        <p style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.65 }}>
          After you continue, the system suggests 3 creative angles. You pick one. Then references. Then mood. You can change any later.
        </p>
      </div>
    </div>
  )
}

const rootStyle: CSSProperties = { animation: "fade-in 0.25s ease" }

const pickerLabelStyle: CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  color: "var(--purple)",
  letterSpacing: "0.1em",
  textTransform: "uppercase",
  marginBottom: 10,
}

const scriptLinkStyle: CSSProperties = {
  background: "none",
  border: "none",
  fontSize: 12,
  color: "var(--accent)",
  padding: 0,
  cursor: "pointer",
  opacity: 0.85,
  textDecoration: "underline",
  textDecorationColor: "rgba(91,127,255,0.35)",
  fontFamily: "inherit",
}

function continueBtnStyle(canSubmit: boolean): CSSProperties {
  return {
    background: canSubmit
      ? "linear-gradient(135deg, var(--accent) 0%, #4a6ee0 100%)"
      : "rgba(91,127,255,0.25)",
    color: canSubmit ? "#fff" : "rgba(255,255,255,0.4)",
    fontWeight: 700,
    fontSize: 13,
    borderRadius: "var(--radius-md)",
    padding: "12px 30px",
    border: "none",
    cursor: canSubmit ? "pointer" : "not-allowed",
    transition: "all 0.2s",
    letterSpacing: "0.01em",
    boxShadow: canSubmit ? "0 2px 12px rgba(91,127,255,0.35)" : "none",
    fontFamily: "inherit",
  }
}

const cancelBtnStyle: CSSProperties = {
  background: "transparent",
  border: "1px solid var(--border2)",
  borderRadius: "var(--radius-md)",
  padding: "8px 14px",
  color: "var(--muted)",
  fontSize: 12,
  cursor: "pointer",
  fontFamily: "inherit",
}

const whatNextStyle: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: "14px 18px",
  marginTop: 24,
  display: "flex",
  gap: 14,
  alignItems: "flex-start",
}

const whatNextLabelStyle: CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  color: "var(--purple)",
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  marginBottom: 5,
}
