interface Props {
  text: string
  ts: string
}

export default function UserMessage({ text, ts }: Props) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '10px 0', justifyContent: 'flex-end' }}>
      <div style={{ maxWidth: '72%' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: 6,
            justifyContent: 'flex-end',
            marginBottom: 5,
          }}
        >
          <span
            style={{
              fontSize: 10,
              color: 'var(--dim)',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {ts}
          </span>
          <span
            style={{
              fontSize: 10,
              fontWeight: 700,
              color: 'var(--green)',
              letterSpacing: '0.07em',
              textTransform: 'uppercase',
            }}
          >
            You
          </span>
        </div>
        <div
          style={{
            background: 'rgba(45,206,122,0.07)',
            border: '1px solid rgba(45,206,122,0.2)',
            borderRadius: '10px 10px 4px 10px',
            padding: '9px 13px',
            fontSize: 12,
            color: 'var(--text)',
            lineHeight: 1.55,
          }}
        >
          {text}
        </div>
      </div>
    </div>
  )
}
