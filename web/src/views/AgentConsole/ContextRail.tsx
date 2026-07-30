import { useProductionStore } from '../../store/productionStore'
import type { AuditEntry, Branch } from '../../types/production'

// â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString(undefined, {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  } catch {
    return ts
  }
}

function eventPrimary(e: AuditEntry): string {
  const actor  = (e.actor || 'system').replace(/Agent$/, '')
  const detail = e.reason ?? e.gate_name ?? (e.action_type ? e.action_type.replace(/_/g, ' ') : 'event')
  return `${actor} Â· ${detail}`
}

// â”€â”€ static fallbacks (shown before first poll) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const MOCK_EVENTS = [
  { ts: '14:22:08', primary: 'system Â· generation done',           secondary: 'â€” shot_7_v3.jsonl' },
  { ts: '14:22:31', primary: 'CD Â· 3 framings proposed',            secondary: null },
  { ts: '14:23:14', primary: 'user Â· approve B (height 1.0m)',      secondary: null },
  { ts: '14:23:21', primary: 'SD Â· reading production stateâ€¦',      secondary: null },
  { ts: '14:23:48', primary: 'RV Â· flagged: expression drift',       secondary: null },
]

// â”€â”€ Section label â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 10,
        fontWeight: 700,
        color: 'var(--purple)',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        marginBottom: 10,
      }}
    >
      {children}
    </div>
  )
}

function Divider() {
  return <div style={{ height: 1, background: 'var(--border)', margin: '0 -14px' }} />
}

// â”€â”€ ContextRail â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function ContextRail() {
  const production   = useProductionStore((s) => s.production)
  const auditEntries = useProductionStore((s) => s.auditEntries)

  const firstScene  = production?.scenes?.[0]
  const firstShot   = firstScene?.shots?.[0]
  const shotLabel   = firstShot
    ? `Shot 1 Â· ${firstShot.camera?.framing ?? 'close'}`
    : 'Shot 7 Â· Close-up'
  const sceneDetail = firstScene
    ? `Scene 1 Â· ${firstShot?.duration_sec ?? 2.1}s`
    : 'Scene 3 Â· 2.1s Â· 85mm Â· 3200K'

  const hasLive   = auditEntries.length > 0
  const recentLive = [...auditEntries]
    .sort((a, b) => (a.ts > b.ts ? -1 : 1))
    .slice(0, 5)

  const liveBranches: Branch[] = production?.branches ?? []

  const lockedDecisions = auditEntries
    .filter((e) => e.decision_status === 'accepted' && e.gate_name)
    .slice(0, 4)

  return (
    <div
      style={{
        width: 460,
        flexShrink: 0,
        background: 'rgba(0,0,0,0.45)',
        borderLeft: '1px solid var(--border)',
        overflowY: 'auto',
        padding: '14px 14px',
        display: 'flex',
        flexDirection: 'column',
        gap: 18,
      }}
    >
      {/* â”€â”€ CONTEXT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section>
        <SectionLabel>Context</SectionLabel>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>{shotLabel}</div>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 3 }}>{sceneDetail}</div>
        {production && (
          <div
            style={{
              fontSize: 10,
              color: 'var(--dim)',
              fontFamily: 'monospace',
              marginTop: 4,
              background: 'var(--surface-1)',
              border: '1px solid var(--border)',
              borderRadius: 4,
              padding: '3px 8px',
              display: 'inline-block',
            }}
          >
            {production.id}
          </div>
        )}
      </section>

      <Divider />

      {/* â”€â”€ RECENT EVENTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section>
        <SectionLabel>Recent events</SectionLabel>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
          {hasLive
            ? recentLive.map((ev, i) => (
                <div key={(ev.id || `evt-${i}`) + `-${i}`} style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
                  <span
                    style={{
                      fontSize: 10,
                      color: 'var(--dim)',
                      flexShrink: 0,
                      fontVariantNumeric: 'tabular-nums',
                      letterSpacing: '0.01em',
                    }}
                  >
                    {formatTs(ev.ts)}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text2)' }}>{eventPrimary(ev)}</span>
                </div>
              ))
            : MOCK_EVENTS.map((ev, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
                    <span
                      style={{
                        fontSize: 10,
                        color: 'var(--dim)',
                        flexShrink: 0,
                        fontVariantNumeric: 'tabular-nums',
                      }}
                    >
                      {ev.ts}
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--text2)' }}>{ev.primary}</span>
                  </div>
                  {ev.secondary && (
                    <div style={{ fontSize: 9, color: 'var(--dim)', paddingLeft: 52, marginTop: 1 }}>
                      {ev.secondary}
                    </div>
                  )}
                </div>
              ))
          }
          <div style={{ fontSize: 9, color: 'var(--dim)', marginTop: 4, fontStyle: 'italic' }}>
            â€” {auditEntries.length || 247} events total in this production
          </div>
        </div>
      </section>

      <Divider />

      {/* â”€â”€ BRANCHES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section>
        <SectionLabel>Branches</SectionLabel>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {liveBranches.length > 0
            ? liveBranches.map((b, i) => (
                <div
                  key={b.id}
                  style={{
                    padding: '3px 9px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 10,
                    fontWeight: 600,
                    background: i === 0 ? 'rgba(157,126,245,0.12)' : 'rgba(255,255,255,0.03)',
                    border: i === 0 ? '1px solid rgba(157,126,245,0.35)' : '1px solid var(--border)',
                    color: i === 0 ? 'var(--purple2)' : 'var(--muted)',
                    cursor: 'pointer',
                  }}
                >
                  {b.name}{i === 0 ? ' â—' : ''}
                </div>
              ))
            : [
                { label: 'main Â· neutral â—', active: true  },
                { label: 'dark-cut',          active: false },
                { label: 'warm-amber',         active: false },
                { label: '+ new branch',       active: false },
              ].map((b) => (
                <div
                  key={b.label}
                  style={{
                    padding: '3px 9px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 10,
                    fontWeight: 600,
                    background: b.active ? 'rgba(157,126,245,0.12)' : 'rgba(255,255,255,0.03)',
                    border: b.active ? '1px solid rgba(157,126,245,0.35)' : '1px solid var(--border)',
                    color: b.active ? 'var(--purple2)' : 'var(--muted)',
                    cursor: 'pointer',
                    transition: 'background 0.15s',
                  }}
                >
                  {b.label}
                </div>
              ))
          }
        </div>
      </section>

      <Divider />

      {/* â”€â”€ LOCKED DECISIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section>
        <SectionLabel>Locked decisions</SectionLabel>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {lockedDecisions.length > 0
            ? lockedDecisions.map((item) => (
                <div key={item.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
                  <span style={{ fontSize: 11, color: 'var(--green)', flexShrink: 0, marginTop: 1 }}>âœ“</span>
                  <span style={{ fontSize: 11, color: 'var(--text2)' }}>
                    {item.gate_name} Â· {item.reason ?? 'accepted'}
                  </span>
                </div>
              ))
            : [
                { done: true,  text: 'mood Â· 90s thriller palette' },
                { done: true,  text: 'temperature Â· 3200K' },
                { done: true,  text: 'protagonist anchor Â· v1 (drift -0.02)' },
                { done: false, text: "director's framing Â· in proposal" },
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 7 }}>
                  <span
                    style={{
                      fontSize: 11,
                      color: item.done ? 'var(--green)' : 'var(--dim)',
                      flexShrink: 0,
                      marginTop: 1,
                    }}
                  >
                    {item.done ? 'âœ“' : 'â€”'}
                  </span>
                  <span
                    style={{
                      fontSize: 11,
                      color: item.done ? 'var(--text2)' : 'var(--dim)',
                      fontStyle: item.done ? 'normal' : 'italic',
                    }}
                  >
                    {item.text}
                  </span>
                </div>
              ))
          }
        </div>
      </section>
    </div>
  )
}


