import { useProductionStore } from "../../../store/productionStore"
import { useState } from "react"
import type { CSSProperties } from "react"

interface Scene {
  name: string
  shots: string[]
}

const FALLBACK: Scene[] = [
  { name: 'Scene 01 - "First Encounter"', shots: ["s1", "s2", "s3", "s4", "s5"] },
  { name: 'Scene 02 - "The Reveal"',      shots: ["s1", "s2", "s3", "s4"] },
  { name: 'Scene 03 - "Aftermath"',       shots: ["s1", "s2", "s3"] },
]

export default function PlanTheProductionStage() {
  const runResult = useProductionStore((s) => s.runResult)
  const [activeShot, setActiveShot] = useState<{ scene: number; shot: number } | null>(null)

  const shotsFromResult = runResult?.shot_plan_result?.shots
  const scenes: Scene[] = FALLBACK  // wire to scenes from shot_plan_result in a later iteration

  const cur = activeShot ?? { scene: 0, shot: 1 }
  const curScene = scenes[cur.scene]

  return (
    <div style={{ animation: "fade-in 0.25s ease" }}>
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--accent)",
          marginBottom: 6,
          letterSpacing: "-0.02em",
        }}
      >
        Plan the Production
      </h1>
      <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 20 }}>
        How will it unfold? The crew drafts scenes + shots + camera. You approve or adjust.
      </p>

      <div style={scenesBox}>
        {scenes.map((s, i) => (
          <SceneRow
            key={i}
            scene={s}
            index={i}
            activeShot={activeShot}
            onShot={(j) => setActiveShot({ scene: i, shot: j })}
          />
        ))}
      </div>

      {curScene && (
        <ShotDetail scene={curScene.name} shotIndex={cur.shot - 1} />
      )}

      <p style={{ fontSize: 11, color: "var(--muted)", marginTop: 14 }}>
        {shotsFromResult
          ? "Shot plan locked. Real frames render in Stage 6."
          : "Plan draft. Approve to lock and pass to Stage 6."}
      </p>
    </div>
  )
}

const scenesBox: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: 12,
  marginBottom: 16,
}

function SceneRow({
  scene,
  index,
  activeShot,
  onShot,
}: {
  scene: Scene
  index: number
  activeShot: { scene: number; shot: number } | null
  onShot: (j: number) => void
}) {
  return (
    <div
      style={{
        padding: "10px 0",
        borderBottom: index < 2 ? "1px solid var(--border)" : "none",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>{scene.name}</span>
        <span style={{ fontSize: 10, color: "var(--dim)", fontFamily: "monospace" }}>
          {scene.shots.length} shots
        </span>
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {scene.shots.map((s, j) => {
          const active = activeShot?.scene === index && activeShot.shot === j + 1
          return (
            <button
              key={j}
              onClick={() => onShot(j + 1)}
              style={shotChipStyle(active)}
              title={"Shot " + (j + 1)}
            >
              {s}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function shotChipStyle(active: boolean): CSSProperties {
  return {
    padding: "4px 10px",
    background: active ? "rgba(91,127,255,0.18)" : "rgba(255,255,255,0.04)",
    border: "1px solid " + (active ? "var(--accent)" : "var(--border2)"),
    borderRadius: "var(--radius-sm)",
    fontSize: 10,
    fontFamily: "monospace",
    color: active ? "var(--accent2)" : "var(--muted)",
    cursor: "pointer",
  }
}

function ShotDetail({ scene, shotIndex }: { scene: string; shotIndex: number }) {
  return (
    <div
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
        padding: 16,
        marginBottom: 16,
      }}
    >
      <p style={{ fontSize: 10, color: "var(--dim)", marginBottom: 8, fontFamily: "monospace" }}>
        {scene} - shot {shotIndex + 1}
      </p>
      <Detail label="Camera" value="35mm, eye-level, dolly-in" />
      <Detail label="Lighting" value="warm key, soft fill, 3200K" />
      <Detail label="Audio" value="voice + ambient cafe + soft music" />
      <div style={storyboardStyle}>
        <pre style={{ fontSize: 10, color: "var(--muted)", lineHeight: 1.2, margin: 0, fontFamily: "monospace" }}>{`+---------------+
|               |
|   [character] |
|               |
+---------------+`}</pre>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button style={detailBtnStyle}>Edit camera</button>
        <button style={detailBtnStyle}>Edit lighting</button>
        <button style={detailBtnStyle}>Edit audio</button>
      </div>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", gap: 12, padding: "4px 0", fontSize: 12 }}>
      <span style={{ color: "var(--muted)", width: 80, flexShrink: 0 }}>{label}</span>
      <span style={{ color: "var(--text)", fontFamily: "monospace" }}>{value}</span>
    </div>
  )
}

const storyboardStyle: CSSProperties = {
  marginTop: 10,
  padding: 12,
  background: "var(--bg2)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  textAlign: "center",
}

const detailBtnStyle: CSSProperties = {
  padding: "5px 10px",
  background: "transparent",
  border: "1px solid var(--border2)",
  borderRadius: "var(--radius-sm)",
  fontSize: 10,
  color: "var(--muted)",
  cursor: "pointer",
  fontFamily: "inherit",
}
