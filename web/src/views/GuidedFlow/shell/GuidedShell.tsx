import { useEffect, useState, type ReactNode, type CSSProperties } from "react"
import StepIndicator from "./StepIndicator"
import CrewActivityStrip from "./CrewActivityStrip"
import RightRail from "./RightRail"
import { STAGES, getStage } from "../data/stageMap"
import { useProductionStore } from "../../../store/productionStore"
import type { CrewMember, CrewStatus } from "../types"

interface Props {
  children: ReactNode
}

interface AdvanceContext {
  angles: ReadonlyArray<{ id: string }>
  chosenAngleId: string | null
  runResult: unknown
}

export function canAdvanceFrom(step: number, ctx: AdvanceContext): boolean {
  switch (step) {
    case 3:
      // HARD gate: must pick an angle before advancing.
      return ctx.chosenAngleId !== null
    default:
      return true
  }
}

export default function GuidedShell({ children }: Props) {
  const flowStep    = useProductionStore((s) => s.flowStep)
  const setFlowStep = useProductionStore((s) => s.setFlowStep)
  const intent      = useProductionStore((s) => s.intent)
  const angles      = useProductionStore((s) => s.angles)
  const chosenAngleId = useProductionStore((s) => s.chosenAngleId)
  const loading     = useProductionStore((s) => s.flowLoading)
  const status      = useProductionStore((s) => s.flowStatus)
  const runResult   = useProductionStore((s) => s.runResult)

  const [selectedAgent, setSelectedAgent] = useState<CrewMember | null>(null)
  const [railOpen, setRailOpen] = useState<boolean>(() =>
    typeof window !== "undefined" ? window.innerWidth >= 1100 : true,
  )

  useEffect(() => {
    function onResize() {
      setRailOpen((open) => (window.innerWidth < 1100 ? false : open))
    }
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  const stage = getStage(flowStep)
  const gateClear = canAdvanceFrom(flowStep, { angles, chosenAngleId, runResult })

  // Keyboard navigation: Arrow Left/Right to move between stages; Escape to close agent detail.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement | null
      if (target) {
        const tag = target.tagName
        if (tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable) return
      }
      if (e.key === "Escape" && selectedAgent) {
        e.preventDefault()
        setSelectedAgent(null)
        return
      }
      if (e.key === "ArrowLeft" && flowStep > 1) {
        e.preventDefault()
        setFlowStep(flowStep - 1)
        return
      }
      if (e.key === "ArrowRight" && flowStep < 7) {
        e.preventDefault()
        if (canAdvanceFrom(flowStep, { angles, chosenAngleId, runResult })) {
          setFlowStep(flowStep + 1)
        }
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [flowStep, selectedAgent, setFlowStep, angles, chosenAngleId, runResult])

  // Compute live crew status from the current stage + store state.
  const liveStatus: Record<string, CrewStatus> = {}
  if (flowStep === 1 && intent.topic.trim().length > 0) liveStatus["research_agent"] = "thinking"
  if (flowStep === 3 && angles.length > 0) liveStatus["creative_reframing"] = "ready"
  if (flowStep === 6 && loading) liveStatus["generation"] = "thinking"

  return (
    <div style={rootStyle}>
      <div style={mainRowStyle}>
        <LeftRail />
        <main style={mainStyle} aria-label={"Stage " + stage.num + " canvas"}>
          <StepIndicator step={flowStep} stages={STAGES} onSelect={(n) => setFlowStep(n)} />
          <div style={canvasInnerStyle}>
            {children}
          </div>
          {status && (
            <p style={statusStyle}>{status}</p>
          )}
        </main>
        {railOpen && (
          <RightRail
            stage={stage}
            selectedAgent={selectedAgent}
            onCloseAgent={() => setSelectedAgent(null)}
            auditEntries={[]}
          />
        )}
      </div>
      <CrewActivityStrip
        liveStatus={liveStatus}
        selectedId={selectedAgent?.id ?? null}
        onSelectAgent={setSelectedAgent}
      />
      <Footer
        step={flowStep}
        stageName={stage.name}
        gate={stage.gate}
        gateClear={gateClear}
        onBack={() => setFlowStep(flowStep - 1)}
        onNext={() => setFlowStep(flowStep + 1)}
      />
      <RailToggle open={railOpen} onToggle={() => setRailOpen((o) => !o)} />
    </div>
  )
}

function LeftRail() {
  const items: Array<{ sym: string; label: string }> = [
    { sym: "\u2302", label: "Home" },
    { sym: "\u270D", label: "Notes" },
    { sym: "\u2318", label: "Command palette" },
  ]
  return (
    <nav aria-label="Guided flow navigation" className="left-rail" style={leftRailStyle}>
      {items.map((it) => (
        <button
          key={it.label}
          title={it.label}
          aria-label={it.label}
          style={leftRailBtnStyle}
        >
          {it.sym}
        </button>
      ))}
    </nav>
  )
}

function RailToggle({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={open ? "Hide help panel" : "Show help panel"}
      aria-pressed={open}
      className="rail-toggle"
      title={open ? "Hide help" : "Show help"}
    >
      {open ? "\u00BB" : "?"}
    </button>
  )
}

interface FooterProps {
  step: number
  stageName: string
  gate: "soft" | "hard"
  gateClear: boolean
  onBack: () => void
  onNext: () => void
}

function Footer({ step, stageName, gate, gateClear, onBack, onNext }: FooterProps) {
  const isLast = step >= 7
  const canGoNext = !isLast && gateClear
  return (
    <footer style={footerStyle}>
      <button
        onClick={onBack}
        disabled={step <= 1}
        style={{ ...footerBtnStyle, opacity: step <= 1 ? 0.4 : 1, cursor: step <= 1 ? "not-allowed" : "pointer" }}
      >
        {"\u2190 Back"}
      </button>
      <div className="footer-label" style={{ flex: 1, textAlign: "center", fontSize: 11, color: "var(--muted)" }}>
        Stage {step} of 7 {"\u00B7"} {stageName}
        {gate === "hard" && !gateClear && (
          <span className="footer-hint" style={{ marginLeft: 10, color: "var(--amber)", fontWeight: 700 }}>
            {"\u2022"} hard gate: complete this stage first
          </span>
        )}
      </div>
      <button
        onClick={onNext}
        disabled={!canGoNext}
        aria-disabled={!canGoNext}
        title={!gateClear ? "Complete this stage first" : undefined}
        style={{
          ...footerBtnStyle,
          background: canGoNext ? "var(--accent)" : "transparent",
          color: canGoNext ? "#fff" : "var(--muted)",
          borderColor: canGoNext ? "var(--accent)" : "var(--border2)",
          opacity: canGoNext ? 1 : 0.45,
          cursor: canGoNext ? "pointer" : "not-allowed",
        }}
      >
        {"Next \u2192"}
      </button>
    </footer>
  )
}

const rootStyle: CSSProperties = {

  flexDirection: "column",
  height: "100%",
  overflow: "hidden",
}

const mainRowStyle: CSSProperties = {
  flex: 1,

  minHeight: 0,
}

const mainStyle: CSSProperties = {
  flex: 1,
  overflowY: "auto",
  padding: "0 24px",
  minWidth: 0,
}

const canvasInnerStyle: CSSProperties = {
  maxWidth: 760,
  margin: "0 auto",
  paddingBottom: 32,
}

const statusStyle: CSSProperties = {
  textAlign: "center",
  fontSize: 11,
  color: "var(--dim)",
  margin: "0 auto 12px",
}

// NOTE: display set via .left-rail class so media queries can override it.
const leftRailStyle: CSSProperties = {
  width: 60,
  flexShrink: 0,
  borderRight: "1px solid var(--border)",
  background: "rgba(0,0,0,0.4)",

  flexDirection: "column",
  alignItems: "center",
  padding: "16px 0",
  gap: 14,
}

const leftRailBtnStyle: CSSProperties = {
  width: 36,
  height: 36,
  borderRadius: "var(--radius-md)",
  background: "transparent",
  border: "1px solid transparent",
  color: "var(--muted)",
  fontSize: 16,
  cursor: "pointer",
  fontFamily: "inherit",
}

const footerStyle: CSSProperties = {
  height: 60,
  borderTop: "1px solid var(--border)",
  background: "rgba(0,0,0,0.4)",

  alignItems: "center",
  padding: "0 20px",
  gap: 16,
}

const footerBtnStyle: CSSProperties = {
  padding: "8px 16px",
  fontSize: 12,
  fontWeight: 600,
  background: "transparent",
  border: "1px solid var(--border2)",
  borderRadius: "var(--radius-md)",
  color: "var(--muted)",
  fontFamily: "inherit",
}

