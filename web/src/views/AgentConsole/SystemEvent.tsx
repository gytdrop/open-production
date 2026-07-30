interface Props {
  message: string
  detail?: string
  ts: string
  duration?: string
}

export default function SystemEvent({ message, detail, ts, duration }: Props) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '8px 0', alignItems: 'flex-start' }}>
      {/* Green status dot */}
      <div style={{ marginTop: 5, flexShrink: 0 }}>
        <div
          style={{
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--green)',
            boxShadow: '0 0 0 2px rgba(45,206,122,0.15)',
          }}
        />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: 'var(--green)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            System
          </span>
          <span style={{ fontSize: 12, color: 'var(--text2)' }}>{message}</span>
          {duration && (
            <span style={{ fontSize: 10, color: 'var(--muted)' }}>· {duration}</span>
          )}
          <span
            style={{
              fontSize: 10,
              color: 'var(--dim)',
              marginLeft: 'auto',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {ts}
          </span>
        </div>
        {detail && (
          <div style={{ fontSize: 10, color: 'var(--dim)', marginTop: 2, paddingLeft: 2 }}>
            — {detail}
          </div>
        )}
      </div>
    </div>
  )
}
