import { CREW } from "../data/crewMembers"
import type { CrewMember, CrewStatus } from "../types"

interface Props {
  liveStatus?: Record<string, CrewStatus>
  selectedId?: string | null
  onSelectAgent?: (agent: CrewMember | null) => void
}

const STATUS_COLOR: Record<CrewStatus, string> = {
  ready:     "var(--green)",
  thinking:  "var(--amber)",
  proposing: "var(--purple)",
  reviewing: "var(--pink)",
  idle:      "var(--dim)",
}

export default function CrewActivityStrip({ liveStatus = {}, selectedId, onSelectAgent }: Props) {
  return (
    <div
      role="region"
      aria-label="Production crew activity"
      style={{
        height: 40,
        borderTop: "1px solid var(--border)",
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        gap: 4,
        padding: "0 12px",
        overflowX: "auto",
      }}
    >
      <span
        style={{
          fontSize: 9,
          fontWeight: 800,
          color: "var(--purple)",
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          marginRight: 8,
          flexShrink: 0,
        }}
      >
        Crew
      </span>
      {CREW.map((member) => {
        const status = liveStatus[member.id] ?? member.defaultStatus
        const isSelected = selectedId === member.id
        return (
          <button
            key={member.id}
            type="button"
            onClick={() => onSelectAgent?.(isSelected ? null : member)}
            title={member.name + " - " + member.role}
            aria-pressed={isSelected}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 8px",
              borderRadius: 20,
              background: isSelected ? "rgba(157,126,245,0.16)" : "transparent",
              border: "1px solid " + (isSelected ? "var(--purple)" : "transparent"),
              cursor: "pointer",
              flexShrink: 0,
              transition: "background 0.15s, border-color 0.15s",
              fontFamily: "inherit",
            }}
          >
            <span
              aria-label={"status " + status}
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: STATUS_COLOR[status],
                flexShrink: 0,
                animation: status === "thinking" ? "status-blink 1.4s ease infinite" : undefined,
              }}
            />
            <span style={{ fontSize: 10, color: "var(--text2)", whiteSpace: "nowrap", fontFamily: "inherit" }}>
              {member.name}
            </span>
          </button>
        )
      })}
    </div>
  )
}
