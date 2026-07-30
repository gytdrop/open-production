import type { FlowStage } from "../types"

interface Props {
  step: number
  stages: FlowStage[]
  onSelect?: (num: number) => void
}

export default function StepIndicator({ step, stages, onSelect }: Props) {
  return (
    <div style={{ textAlign: "center", padding: "20px 0 12px" }}>
      <p
        style={{
          fontSize: 10,
          fontWeight: 700,
          color: "var(--dim)",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          marginBottom: 14,
        }}
      >
        Step {step} of {stages.length}
      </p>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 0 }}>
        {stages.map((s, i) => {
          const num = s.num
          const isDone = num < step
          const isActive = num === step
          const isFuture = num > step
          const handleClick = onSelect && (isDone || isActive) ? () => onSelect(num) : undefined
          const dotBg = isDone
            ? "linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%)"
            : isActive
              ? "linear-gradient(135deg, var(--" + s.accentVar.replace("--", "") + ") 0%, var(--purple) 100%)"
              : "transparent"
          return (
            <div key={s.slug} style={{ display: "flex", alignItems: "center" }}>
              {i > 0 && (
                <div
                  style={{
                    width: 28,
                    height: 2,
                    background: isDone
                      ? "linear-gradient(90deg, var(--accent) 0%, var(--accent2) 100%)"
                      : "var(--border2)",
                    borderRadius: 1,
                    opacity: isFuture ? 0.35 : 1,
                  }}
                />
              )}
              <div
                onClick={handleClick}
                title={s.name}
                role="button"
                aria-label={"Step " + num + ": " + s.name}
                tabIndex={handleClick ? 0 : -1}
                onKeyDown={(e) => {
                  if (handleClick && (e.key === "Enter" || e.key === " ")) {
                    e.preventDefault()
                    handleClick()
                  }
                }}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 6,
                  cursor: handleClick ? "pointer" : "default",
                }}
              >
                <div
                  style={{
                    width: isDone || isActive ? 22 : 12,
                    height: isDone || isActive ? 22 : 12,
                    borderRadius: "50%",
                    background: dotBg,
                    border: isFuture ? "1.5px solid var(--border2)" : "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 10,
                    fontWeight: 800,
                    color: isDone || isActive ? "#fff" : "var(--dim)",
                    boxShadow: isActive
                      ? "0 0 0 4px var(--accent-glow), 0 0 14px var(--accent-glow)"
                      : undefined,
                  }}
                >
                  {isDone ? "✓" : num}
                </div>
                <span
                  style={{
                    fontSize: 9,
                    fontWeight: isActive ? 700 : 400,
                    color: isActive ? "var(--text)" : isDone ? "var(--accent2)" : "var(--dim)",
                    opacity: isFuture ? 0.4 : 1,
                    whiteSpace: "nowrap",
                  }}
                >
                  {shortLabel(s.name)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function shortLabel(name: string): string {
  const words = name.split(" ")
  return words[words.length - 1]
}
