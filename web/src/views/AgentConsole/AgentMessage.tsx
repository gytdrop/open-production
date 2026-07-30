import type { ReactNode } from 'react'

interface Props {
  agent: string
  initials: string
  avatarColor: string
  ts?: string
  subtitle?: string
  thinking?: boolean
  children?: ReactNode
}

export default function AgentMessage({ agent, initials, avatarColor, ts, subtitle, thinking, children }: Props) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '10px 0', alignItems: 'flex-start' }}>
      {/* Avatar */}
      <div style={{ position: 'relative', flexShrink: 0 }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: avatarColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 9,
            fontWeight: 700,
            color: '#fff',
            letterSpacing: '0.03em',
            flexShrink: 0,
          }}
        >
          {initials}
        </div>
        {thinking && (
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              right: 0,
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--amber)',
              border: '1.5px solid var(--bg)',
              animation: 'status-blink 1s ease infinite',
            }}
          />
        )}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 5 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)' }}>{agent}</span>
          {ts && <span style={{ fontSize: 10, color: 'var(--dim)', fontVariantNumeric: 'tabular-nums' }}>{ts}</span>}
          {subtitle && <span style={{ fontSize: 10, color: 'var(--muted)' }}>· {subtitle}</span>}
        </div>
        {/* Message bubble */}
        {children && (
          <div
            style={{
              background: 'var(--surface-1)',
              border: '1px solid var(--border)',
              borderRadius: '4px 10px 10px 10px',
              padding: '10px 14px',
            }}
          >
            {children}
          </div>
        )}
      </div>
    </div>
  )
}
