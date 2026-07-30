import { useState } from 'react'

type FlagState = 'idle' | 'regenerating' | 'overridden'

export default function ReviewerFlag() {
  const [state, setState] = useState<FlagState>('idle')

  return (
    <div
      style={{
        background: 'rgba(240,98,146,0.05)',
        border: '1px solid rgba(240,98,146,0.25)',
        borderRadius: 'var(--radius-md)',
        padding: '12px 14px',
      }}
    >
      {/* Flag header */}
      <div
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: 'var(--pink)',
          marginBottom: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <span style={{ fontSize: 11 }}>⚠</span>
        Character expression diverges from anchor
      </div>

      <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 4, lineHeight: 1.65 }}>
        Generated S07_03 is 0.34 cosine-similarity off from protagonist.v1 anchor.
        <br />
        Suggest re-generating or accepting with override annotation.
      </div>

      <div style={{ fontSize: 10, color: 'var(--dim)', fontStyle: 'italic', marginBottom: 12 }}>
        Either choice is recorded in the audit trail.
      </div>

      {state === 'overridden' ? (
        <div
          style={{
            fontSize: 11,
            color: 'var(--green)',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
          }}
        >
          <span>✓</span> Override recorded in audit trail.
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setState('regenerating')}
            disabled={state === 'regenerating'}
            style={{
              padding: '5px 13px',
              fontSize: 11,
              fontWeight: 600,
              background: state === 'regenerating' ? 'rgba(255,255,255,0.04)' : 'rgba(240,98,146,0.10)',
              border: `1px solid ${state === 'regenerating' ? 'var(--border)' : 'rgba(240,98,146,0.35)'}`,
              borderRadius: 'var(--radius-sm)',
              color: state === 'regenerating' ? 'var(--dim)' : 'var(--pink)',
              cursor: state === 'regenerating' ? 'default' : 'pointer',
              transition: 'all 0.15s',
            }}
          >
            {state === 'regenerating' ? '✓ Re-generating…' : 'Re-generate'}
          </button>
          <button
            onClick={() => setState('overridden')}
            style={{
              padding: '5px 13px',
              fontSize: 11,
              fontWeight: 600,
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border2)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text2)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            Accept + Override
          </button>
        </div>
      )}
    </div>
  )
}
