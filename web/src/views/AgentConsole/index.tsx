import { useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useProductionStore } from '../../store/productionStore'
import { useAuditPoll } from '../../hooks/useAuditPoll'
import CrewRail from './CrewRail'
import ConversationThread from './ConversationThread'
import ContextRail from './ContextRail'
import ShotStrip from './ShotStrip'
import CommandBar from './CommandBar'
import StateMachineBadge from '../../components/StateMachineBadge'

// ── Status bar cells ─────────────────────────────────────────────────────────

interface StatusCell {
  label: string
  value: string
  color: string
}

function buildStatusCells(
  production: ReturnType<typeof useProductionStore.getState>['production'],
  auditCount: number,
): StatusCell[] {
  const state    = production?.state
  const scenes   = production?.scenes ?? []
  const totalShots = scenes.reduce((n, s) => n + (s?.shots?.length ?? 0), 0)
  const branches = production?.branches ?? []

  return [
    { label: 'Stage',        value: state ? `${state}` : '16 / 26 · review',                              color: 'var(--text2)' },
    { label: 'Crew',         value: '8 ready · 1 thinking',                                                color: 'var(--green)' },
    { label: 'Reviewer',     value: '1 finding · 0 override',                                              color: 'var(--pink)' },
    { label: 'Branches',     value: branches.length > 0 ? `${branches.length} branches` : 'main + 2',     color: 'var(--text2)' },
    { label: 'Audit',        value: `${auditCount > 0 ? auditCount : totalShots || 249} events`,           color: 'var(--text2)' },
  ]
}

// ── AgentConsole view ─────────────────────────────────────────────────────────

export default function AgentConsole() {
  const [searchParams] = useSearchParams()
  const urlId = searchParams.get('id')

  const setProductionId = useProductionStore((s) => s.setProductionId)
  const productionId    = useProductionStore((s) => s.productionId)
  const production      = useProductionStore((s) => s.production)
  const auditEntries    = useProductionStore((s) => s.auditEntries)
  const consoleError    = useProductionStore((s) => s.consoleError)

  useEffect(() => {
    if (urlId) setProductionId(urlId)
  }, [urlId, setProductionId])

  useAuditPoll(productionId ?? urlId)

  const hasData = auditEntries.length > 0 || !!production

  // ── Error state ──────────────────────────────────────────────────────────────
  if (consoleError && !hasData) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          color: 'var(--muted)',
          height: 'calc(100vh - 56px)',
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'rgba(240,98,146,0.08)',
            border: '1px solid rgba(240,98,146,0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            color: 'var(--pink)',
          }}
        >
          ⚠
        </div>
        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--pink)' }}>{consoleError}</p>
        <p style={{ fontSize: 12 }}>
          <Link to="/flow" style={{ color: 'var(--accent)', textDecoration: 'underline' }}>
            ← Back to Guided Flow
          </Link>
        </p>
      </div>
    )
  }

  // ── Empty state ──────────────────────────────────────────────────────────────
  if (!productionId && !urlId && !hasData) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          color: 'var(--muted)',
          height: 'calc(100vh - 56px)',
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 22,
          }}
        >
          🎬
        </div>
        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>No production loaded.</p>
        <p style={{ fontSize: 12 }}>
          Start one from{' '}
          <Link to="/flow" style={{ color: 'var(--accent)', textDecoration: 'underline' }}>
            Guided Flow
          </Link>
          .
        </p>
      </div>
    )
  }

  const statusCells = buildStatusCells(production, auditEntries.length)

  return (
    <>
      {/* Outer wrapper: full viewport below NavBar, above status bar */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          paddingBottom: 36,
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {/* ── Left: CrewRail ── */}
        <div className="crew-rail-wrap">
          <CrewRail />
        </div>

        {/* ── Center: ConversationThread + ShotStrip + CommandBar ── */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minWidth: 0,
            overflow: 'hidden',
          }}
        >
          {/* Production state badge */}
          {production && (
            <div
              style={{
                padding: '6px 16px',
                borderBottom: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                background: 'rgba(0,0,0,0.2)',
                flexShrink: 0,
              }}
            >
              <span style={{ fontSize: 10, color: 'var(--dim)', letterSpacing: '0.05em' }}>State</span>
              <StateMachineBadge state={production.state} />
              <span
                style={{
                  fontSize: 10,
                  color: 'var(--dim)',
                  marginLeft: 8,
                  fontFamily: 'monospace',
                  letterSpacing: '0.02em',
                }}
              >
                {production.id}
              </span>
            </div>
          )}
          <ConversationThread />
          <ShotStrip />
          <CommandBar />
        </div>

        {/* ── Right: ContextRail ── */}
        <div className="context-rail-wrap">
          <ContextRail />
        </div>

        {/* ── Status bar (fixed, 36px) ── */}
        <div
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            height: 36,
            background: 'rgba(8,10,15,0.92)',
            borderTop: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            zIndex: 50,
            backdropFilter: 'blur(6px)',
          }}
        >
          {statusCells.map((cell, i) => (
            <div
              key={cell.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '0 16px',
                borderRight: i < statusCells.length - 1 ? '1px solid var(--border)' : 'none',
                flexShrink: 0,
              }}
            >
              <span
                className="status-label"
                style={{
                  fontSize: 9,
                  fontWeight: 700,
                  color: 'var(--dim)',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                }}
              >
                {cell.label}
              </span>
              <span style={{ fontSize: 11, fontWeight: 600, color: cell.color }}>
                {cell.value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Responsive styles ── */}
      <style>{`
        @media (max-width: 1200px) {
          .context-rail-wrap { display: none; }
        }
        @media (max-width: 900px) {
          .crew-rail-wrap > div { width: 40px !important; }
          .crew-rail-wrap [style*="font-size: 11"] { display: none; }
          .crew-rail-wrap [style*="font-size:11"]  { display: none; }
          .crew-rail-wrap [style*="font-size: 9"]  { display: none; }
          .crew-rail-wrap [style*="font-size:9"]   { display: none; }
          .crew-rail-wrap [style*="font-size: 10"] { display: none; }
          .crew-rail-wrap [style*="font-style"]    { display: none; }
        }
        @media (max-width: 640px) {
          .status-label { display: none; }
        }
      `}</style>
    </>
  )
}
