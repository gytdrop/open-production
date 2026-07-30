import { useProductionStore } from '../../store/productionStore'

type AgentStatus = 'active' | 'idle' | 'thinking' | 'flagged' | 'standby'

interface Agent {
  initials: string
  name: string
  fullName: string
  dotColor: string
  status: AgentStatus
  statusText: string
  icon?: string
}

const AGENTS: Agent[] = [
  { initials: 'CD', name: 'Creative Dir.',   fullName: 'Creative Director',  dotColor: 'var(--accent)',  status: 'active',   statusText: 'selected' },
  { initials: 'PR', name: 'Producer',        fullName: 'Producer',           dotColor: 'var(--green)',   status: 'idle',     statusText: 'ready' },
  { initials: 'SB', name: 'Storyboard',      fullName: 'Storyboard Artist',  dotColor: 'var(--green)',   status: 'idle',     statusText: 'ready' },
  { initials: 'SD', name: 'Shot Designer',   fullName: 'Shot Designer',      dotColor: 'var(--amber)',   status: 'thinking', statusText: 'thinking…', icon: '⚡' },
  { initials: 'CH', name: 'Character Dir.',  fullName: 'Character Director', dotColor: 'var(--green)',   status: 'idle',     statusText: 'ready' },
  { initials: 'EA', name: 'Env Artist',      fullName: 'Environment Artist', dotColor: 'var(--green)',   status: 'idle',     statusText: 'ready' },
  { initials: 'ED', name: 'Editor',          fullName: 'Editor',             dotColor: 'var(--green)',   status: 'idle',     statusText: 'ready' },
  { initials: 'CO', name: 'Colorist',        fullName: 'Colorist',           dotColor: 'var(--green)',   status: 'idle',     statusText: 'ready' },
  { initials: 'RV', name: 'Reviewer',        fullName: 'Reviewer',           dotColor: 'var(--pink)',    status: 'flagged',  statusText: '1 finding', icon: '⚠' },
  { initials: 'VD', name: 'Voice Dir.',      fullName: 'Voice Director',     dotColor: 'var(--dim)',     status: 'standby',  statusText: 'standby' },
  { initials: 'MC', name: 'Music Composer',  fullName: 'Music Composer',     dotColor: 'var(--dim)',     status: 'standby',  statusText: 'standby' },
  { initials: 'SN', name: 'Sound Designer',  fullName: 'Sound Designer',     dotColor: 'var(--dim)',     status: 'standby',  statusText: 'standby' },
]

const STATUS_ROW_BG: Record<AgentStatus, string> = {
  active:   'rgba(91,127,255,0.10)',
  idle:     'transparent',
  thinking: 'rgba(245,166,35,0.06)',
  flagged:  'rgba(240,98,146,0.06)',
  standby:  'transparent',
}

const STATUS_ROW_BORDER: Record<AgentStatus, string> = {
  active:   '1px solid rgba(91,127,255,0.28)',
  idle:     '1px solid transparent',
  thinking: '1px solid rgba(245,166,35,0.2)',
  flagged:  '1px solid rgba(240,98,146,0.2)',
  standby:  '1px solid transparent',
}

const STATUS_TEXT: Record<AgentStatus, string> = {
  active:   'var(--accent2)',
  idle:     'var(--green)',
  thinking: 'var(--amber)',
  flagged:  'var(--pink)',
  standby:  'var(--dim)',
}

const AVATAR_BG: Record<AgentStatus, string> = {
  active:   '#1e3a7a',
  idle:     '#192236',
  thinking: '#3d2a06',
  flagged:  '#3d0f27',
  standby:  '#161b27',
}

export default function CrewRail() {
  const selectedActor    = useProductionStore((s) => s.selectedActor)
  const setSelectedActor = useProductionStore((s) => s.setSelectedActor)

  const activeCount  = AGENTS.filter((a) => a.status !== 'standby').length
  const standbyCount = AGENTS.filter((a) => a.status === 'standby').length

  return (
    <div
      style={{
        width: 220,
        flexShrink: 0,
        background: 'rgba(0,0,0,0.45)',
        borderRight: '1px solid var(--border)',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 14px 8px',
          flexShrink: 0,
          borderBottom: '1px solid var(--border)',
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--purple)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          Crew
        </span>
        <span style={{ fontSize: 9, color: 'var(--dim)' }}>
          <span style={{ color: 'var(--green)', fontWeight: 700 }}>{activeCount}</span>
          <span style={{ color: 'var(--dim)' }}> / {AGENTS.length}</span>
        </span>
      </div>

      {/* Agent rows */}
      <div style={{ flex: 1, overflow: 'auto', padding: '6px 6px 0' }}>
        {AGENTS.map((agent) => {
          const isSelected = selectedActor === agent.fullName
          const rowBg      = isSelected ? 'rgba(91,127,255,0.16)' : STATUS_ROW_BG[agent.status]
          const rowBorder  = isSelected ? '1px solid rgba(91,127,255,0.45)' : STATUS_ROW_BORDER[agent.status]

          return (
            <button
              key={agent.initials}
              onClick={() => setSelectedActor(isSelected ? null : agent.fullName)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                width: '100%',
                padding: '7px 8px',
                borderRadius: 'var(--radius-md)',
                background: rowBg,
                border: rowBorder,
                marginBottom: 2,
                cursor: 'pointer',
                textAlign: 'left',
                opacity: agent.status === 'standby' ? 0.4 : 1,
                transition: 'background 0.15s, border-color 0.15s, opacity 0.15s',
              }}
            >
              {/* Avatar with status dot */}
              <div style={{ position: 'relative', flexShrink: 0 }}>
                <div
                  style={{
                    width: 26,
                    height: 26,
                    borderRadius: '50%',
                    background: isSelected ? '#1e3a7a' : AVATAR_BG[agent.status],
                    border: `1.5px solid ${agent.dotColor}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 9,
                    fontWeight: 700,
                    color: 'var(--text)',
                    letterSpacing: '0.02em',
                  }}
                >
                  {agent.initials}
                </div>
                {/* Status dot */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: -1,
                    right: -1,
                    width: 7,
                    height: 7,
                    borderRadius: '50%',
                    background: agent.dotColor,
                    border: '1.5px solid var(--bg)',
                    animation: agent.status === 'thinking' ? 'status-blink 1s ease infinite' : undefined,
                  }}
                />
              </div>

              {/* Name + status */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: isSelected ? 'var(--text)' : 'var(--text2)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  {agent.name}
                  {agent.icon && (
                    <span
                      style={{
                        fontSize: 9,
                        color: agent.status === 'thinking' ? 'var(--amber)' : 'var(--pink)',
                        animation: agent.status === 'thinking' ? 'status-blink 1s ease infinite' : undefined,
                      }}
                    >
                      {agent.icon}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 10, color: STATUS_TEXT[agent.status], marginTop: 1 }}>
                  {agent.statusText}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ padding: '8px 14px 12px', flexShrink: 0, borderTop: '1px solid var(--border)' }}>
        <span style={{ fontSize: 10, color: 'var(--dim)', fontStyle: 'italic' }}>
          + {standbyCount} on standby
        </span>
      </div>
    </div>
  )
}
