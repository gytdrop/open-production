interface Props {
  statusText?: string
}

export default function ThinkingBubble({ statusText = 'Resolving camera spec for option B…' }: Props) {
  return (
    <div
      style={{
        background: 'rgba(77,208,225,0.04)',
        border: '1px solid rgba(77,208,225,0.15)',
        borderRadius: '4px 10px 10px 10px',
        padding: '10px 14px',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}
    >
      {/* 3 animated dots */}
      <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexShrink: 0 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 5,
              height: 5,
              borderRadius: '50%',
              background: 'var(--cyan)',
              animation: `thinking-dot 1.2s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
      <span style={{ fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>{statusText}</span>

      <style>{`
        @keyframes thinking-dot {
          0%, 60%, 100% { opacity: 0.15; transform: scale(0.8); }
          30% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  )
}
