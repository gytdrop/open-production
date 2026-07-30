import { useProductionStore } from '../../store/productionStore'
import type { Shot } from '../../types/production'

// ── Shot status → visual style ────────────────────────────────────────────────

function shotStyle(shot: Shot, index: number): { bg: string; border: string; label: string; labelColor: string } {
  const num = `S${String(index + 1).padStart(2, '0')}`

  switch (shot.status) {
    case 'approved':
    case 'generated':
      return { bg: 'rgba(45,206,122,0.28)', border: '1px solid rgba(45,206,122,0.35)', label: `${num}`, labelColor: 'var(--green2)' }
    case 'in_review':
    case 'in_production':
      return { bg: 'rgba(91,127,255,0.35)',  border: '2px solid var(--accent)',           label: `${num} ▶`, labelColor: 'var(--accent2)' }
    case 'rejected':
      return { bg: 'rgba(245,166,35,0.28)',  border: '1px solid rgba(245,166,35,0.35)',   label: `${num} ⚠`, labelColor: 'var(--amber2)' }
    default: // draft
      return { bg: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)',           label: num,         labelColor: 'var(--dim)' }
  }
}

// ── Static fallback ───────────────────────────────────────────────────────────

const STATIC_SHOTS = [
  { id: 'S01', label: 'S01', icon: '✓', bg: 'rgba(45,206,122,0.28)',  border: '1px solid rgba(45,206,122,0.35)', color: 'var(--green2)' },
  { id: 'S02', label: 'S02', icon: '✓', bg: 'rgba(45,206,122,0.28)',  border: '1px solid rgba(45,206,122,0.35)', color: 'var(--green2)' },
  { id: 'S03', label: 'S03', icon: '✓', bg: 'rgba(45,206,122,0.28)',  border: '1px solid rgba(45,206,122,0.35)', color: 'var(--green2)' },
  { id: 'S04', label: 'S04', icon: '✓', bg: 'rgba(45,206,122,0.28)',  border: '1px solid rgba(45,206,122,0.35)', color: 'var(--green2)' },
  { id: 'S05', label: 'S05', icon: '▶', bg: 'rgba(91,127,255,0.35)',  border: '2px solid var(--accent)',         color: 'var(--accent2)' },
  { id: 'S06', label: 'S06', icon: '⚠', bg: 'rgba(245,166,35,0.28)', border: '1px solid rgba(245,166,35,0.35)', color: 'var(--amber2)' },
]

// ── ShotStrip ─────────────────────────────────────────────────────────────────

export default function ShotStrip() {
  const production = useProductionStore((s) => s.production)

  const liveShots = production?.scenes?.[0]?.shots ?? []
  const hasLive   = liveShots.length > 0

  const sceneName = production?.scenes?.[0]?.name
    ? production.scenes[0].name.toUpperCase()
    : 'SCENE 3'

  return (
    <div
      style={{
        borderTop: '1px solid var(--border)',
        background: 'rgba(0,0,0,0.55)',
        padding: '8px 14px 10px',
        flexShrink: 0,
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 7,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: 'var(--purple)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
            }}
          >
            Shots
          </span>
          <span style={{ fontSize: 10, color: 'var(--dim)' }}>· {sceneName}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <kbd
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: 'var(--purple)',
              background: 'rgba(157,126,245,0.08)',
              border: '1px solid rgba(157,126,245,0.2)',
              borderRadius: 4,
              padding: '2px 6px',
              letterSpacing: '0.02em',
            }}
          >
            ⌘K
          </kbd>
          <span style={{ fontSize: 10, color: 'var(--dim)' }}>command palette</span>
        </div>
      </div>

      {/* Shot tiles */}
      <div style={{ display: 'flex', gap: 5 }}>
        {hasLive
          ? liveShots.slice(0, 12).map((shot, i) => {
              const { bg, border, label, labelColor } = shotStyle(shot, i)
              return (
                <div
                  key={shot.id}
                  title={shot.intent}
                  style={{
                    flex: 1,
                    height: 34,
                    background: bg,
                    border,
                    borderRadius: 5,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 10,
                    fontWeight: 700,
                    color: labelColor,
                    letterSpacing: '0.05em',
                    minWidth: 36,
                  }}
                >
                  {label}
                </div>
              )
            })
          : STATIC_SHOTS.map((shot) => (
              <div
                key={shot.id}
                style={{
                  flex: 1,
                  height: 34,
                  background: shot.bg,
                  border: shot.border,
                  borderRadius: 5,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 1,
                  minWidth: 36,
                }}
              >
                <span style={{ fontSize: 10, fontWeight: 700, color: shot.color, letterSpacing: '0.04em' }}>
                  {shot.label}
                </span>
                <span style={{ fontSize: 8, color: shot.color, opacity: 0.7 }}>{shot.icon}</span>
              </div>
            ))
        }
      </div>
    </div>
  )
}
