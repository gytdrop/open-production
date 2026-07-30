import { useProductionStore } from "../../../store/productionStore"
import type { CSSProperties } from "react"

export default function BuildYourWorldStage() {
  const runResult = useProductionStore((s) => s.runResult)

  const envs = (runResult?.env_result?.proposals ?? []) as Array<{ id?: string; name?: string; location_type?: string; lighting?: string; time_of_day?: string }>
  const moodboard = (runResult?.moodboard_result?.proposals ?? []) as Array<unknown>

  return (
    <div style={{ animation: "fade-in 0.25s ease" }}>
      <h1
        style={{
          fontSize: 26,
          fontWeight: 700,
          color: "var(--green)",
          marginBottom: 6,
          letterSpacing: "-0.02em",
        }}
      >
        Build Your World
      </h1>
      <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 28 }}>
        Characters, locations, and consistency contracts that make the universe.
      </p>

      <SectionHeading>Characters</SectionHeading>
      <div style={gridStyle}>
        {[0, 1, 2].map((i) => (
          <CharacterCard key={i} index={i} />
        ))}
      </div>

      <SectionHeading>Locations</SectionHeading>
      <div style={gridStyle}>
        {envs.length > 0
          ? envs.slice(0, 4).map((e, i) => (
              <LocationCard
                key={i}
                name={e.name ?? ("Location " + (i + 1))}
                time={e.time_of_day ?? "time of day"}
                light={e.lighting ?? "lighting"}
              />
            ))
          : [<LocationCard key="l1" name="Cafe interior" time="dusk" light="warm" />, <LocationCard key="l2" name="Street exterior" time="noon" light="harsh" />]}
      </div>

      <SectionHeading>Mood palette</SectionHeading>
      <div style={paletteRow}>
        {["var(--amber)", "var(--cyan)", "var(--green)", "var(--purple)", "var(--pink)"].map((c, i) => (
          <span
            key={i}
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              background: c,
              border: "2px solid var(--border2)",
            }}
            title={c}
          />
        ))}
      </div>
      <p style={{ fontSize: 11, color: "var(--muted)", marginTop: 8 }}>
        {moodboard.length > 0 ? "MoodSpec locked." : "MoodSpec pending - CharacterDirector will lock once all profiles are confirmed."}
      </p>
    </div>
  )
}

const gridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
  gap: 12,
  marginBottom: 24,
}

const paletteRow: CSSProperties = {
  display: "flex",
  gap: 8,
  marginBottom: 16,
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3
      style={{
        fontSize: 11,
        fontWeight: 700,
        color: "var(--green)",
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        marginBottom: 10,
        marginTop: 8,
      }}
    >
      {children}
    </h3>
  )
}

function CharacterCard({ index }: { index: number }) {
  const names = ["Maya", "Barista", "Regular"]
  const roles = ["(filmmaker)", "(curious)", "(mystery AI)"]
  const voices = ["warm", "brisk", "synth"]
  return (
    <article style={cardStyle}>
      <div style={portraitStyle} />
      <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text)" }}>{names[index] ?? ("Char " + (index + 1))}</p>
      <p style={{ fontSize: 11, color: "var(--muted)" }}>{roles[index] ?? "role"}</p>
      <p style={{ fontSize: 10, color: "var(--dim)", fontFamily: "monospace", marginTop: 2 }}>
        voice: {voices[index] ?? "neutral"}
      </p>
      <button style={editBtnStyle}>Edit</button>
    </article>
  )
}

function LocationCard({ name, time, light }: { name: string; time: string; light: string }) {
  return (
    <article style={cardStyle}>
      <div style={moodStyle} />
      <p style={{ fontSize: 13, fontWeight: 700, color: "var(--text)" }}>{name}</p>
      <p style={{ fontSize: 11, color: "var(--muted)" }}>time: {time}</p>
      <p style={{ fontSize: 10, color: "var(--dim)", fontFamily: "monospace", marginTop: 2 }}>
        light: {light}
      </p>
      <button style={editBtnStyle}>Edit</button>
    </article>
  )
}

const cardStyle: CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: 12,
  display: "flex",
  flexDirection: "column",
  gap: 4,
}

const portraitStyle: CSSProperties = {
  height: 80,
  background: "linear-gradient(135deg, var(--surface-2), var(--surface-3))",
  borderRadius: "var(--radius-sm)",
  marginBottom: 8,
}

const moodStyle: CSSProperties = {
  height: 60,
  background: "linear-gradient(135deg, var(--surface-2), var(--surface-3))",
  borderRadius: "var(--radius-sm)",
  marginBottom: 8,
}

const editBtnStyle: CSSProperties = {
  marginTop: 6,
  padding: "4px 8px",
  background: "transparent",
  border: "1px solid var(--border2)",
  borderRadius: "var(--radius-sm)",
  color: "var(--muted)",
  fontSize: 10,
  cursor: "pointer",
  alignSelf: "flex-start",
  fontFamily: "inherit",
}
