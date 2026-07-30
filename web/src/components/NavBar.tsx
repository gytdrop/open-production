import { useLocation, NavLink } from 'react-router-dom'
import { useProductionStore } from '../store/productionStore'

const ROUTE_META: Record<string, { label: string; code: string; persona: string; sub: string }> = {
  '/flow': {
    label: 'Production Studio',
    code: '02 / GUIDED FLOW',
    persona: 'Production Designer',
    sub: 'Multi-agent pipeline',
  },
  '/console': {
    label: 'Agent Console',
    code: '04 / AGENT CONSOLE',
    persona: 'Technical Director',
    sub: 'Live audit stream',
  },
}

export default function NavBar() {
  const { pathname } = useLocation()
  const productionId = useProductionStore((s) => s.productionId)

  const consoleTarget = productionId ? `/console?id=${encodeURIComponent(productionId)}` : '/console'

  const meta = ROUTE_META[pathname] ?? ROUTE_META['/flow']

  return (
    <header
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: 56,
        background: 'rgba(11,13,18,0.85)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'stretch',
        zIndex: 100,
      }}
    >
      {/* Left accent stripe */}
      <div
        style={{
          width: 3,
          background: 'linear-gradient(180deg, var(--accent) 0%, var(--purple) 100%)',
          flexShrink: 0,
        }}
      />

      {/* Brand */}
      <div
        style={{
          padding: '0 20px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          gap: 1,
          flexShrink: 0,
          borderRight: '1px solid var(--border)',
        }}
      >
        <span
          style={{
            fontSize: 9,
            fontWeight: 800,
            color: 'var(--accent)',
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
          }}
        >
          Open Production
        </span>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.01em' }}>
          {meta.label}
        </span>
      </div>

      {/* Center nav tabs */}
      <nav style={{ flex: 1, display: 'flex', alignItems: 'stretch', justifyContent: 'center', gap: 2, padding: '0 8px' }}>
        {[
          { to: '/flow', label: 'Guided Flow' },
          { to: consoleTarget, label: 'Agent Console', base: '/console' },
        ].map(({ to, label, base }) => (
          <NavLink
            key={label}
            to={to}
            style={({ isActive: navActive }) => {
              const active = navActive || (base && pathname.startsWith(base))
              return {
                padding: '0 18px',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                fontSize: 12,
                fontWeight: 600,
                letterSpacing: '0.02em',
                textDecoration: 'none',
                color: active ? 'var(--text)' : 'var(--muted)',
                borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
                borderTop: '2px solid transparent',
                transition: 'color 0.15s, border-color 0.15s',
                position: 'relative',
              } as React.CSSProperties
            }}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Right meta section */}
      <div
        style={{
          padding: '0 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 20,
          flexShrink: 0,
          borderLeft: '1px solid var(--border)',
        }}
      >
        {/* Live indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: 'var(--green)',
              animation: 'status-blink 2.5s ease infinite',
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--green)', letterSpacing: '0.06em' }}>
            LIVE
          </span>
        </div>

        {/* View meta */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--purple)', letterSpacing: '0.06em' }}>
            {meta.code}
          </span>
          <span style={{ fontSize: 10, color: 'var(--muted)' }}>{meta.persona}</span>
        </div>
      </div>
    </header>
  )
}
