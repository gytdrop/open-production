import type { Angle } from '@/types/production'

export type ProposalAction = 'approve' | 'adjust' | 'override'

interface Props {
  /** The 3 angle options from /api/reframe */
  angles: Angle[]
  /** Currently highlighted option index (0-based) */
  selectedIndex?: number
  onSelect?: (index: number) => void
  onApprove?: (angleId: string) => void
  onAdjust?: (angleId: string) => void
  onOverride?: (angleId: string) => void
  /** Disable all actions while pipeline is running */
  disabled?: boolean
}

const TAG_STYLES: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '1px 6px',
  borderRadius: 3,
  fontSize: 10,
  fontWeight: 600,
  letterSpacing: '0.04em',
  background: 'rgba(107,142,255,.12)',
  color: '#a7c8ff',
}

const BTN: React.CSSProperties = {
  padding: '5px 14px',
  borderRadius: 4,
  fontSize: 12,
  fontWeight: 600,
  border: 'none',
  cursor: 'pointer',
}

export default function ProposalCard({
  angles,
  selectedIndex = 0,
  onSelect,
  onApprove,
  onAdjust,
  onOverride,
  disabled = false,
}: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {angles.map((angle, i) => {
        const isSelected = i === selectedIndex
        return (
          <div
            key={angle.id}
            onClick={() => !disabled && onSelect?.(i)}
            style={{
              padding: '12px 14px',
              borderRadius: 6,
              border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
              background: isSelected ? 'rgba(107,142,255,.07)' : 'var(--panel)',
              cursor: disabled ? 'default' : 'pointer',
              transition: 'border-color 0.15s, background 0.15s',
            }}
          >
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span
                style={{
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 11,
                  fontWeight: 700,
                  background: isSelected ? 'var(--accent)' : 'rgba(255,255,255,.08)',
                  color: isSelected ? '#fff' : 'var(--muted)',
                  flexShrink: 0,
                }}
              >
                {i + 1}
              </span>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{angle.name}</span>
              <span style={{ ...TAG_STYLES, marginLeft: 'auto' }}>{angle.risk_focus}</span>
            </div>

            {/* Summary */}
            <p style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6, lineHeight: 1.5 }}>
              {angle.summary}
            </p>

            {/* Questions */}
            {angle.questions_to_address.length > 0 && (
              <ul style={{ paddingLeft: 16, margin: 0, listStyle: 'disc' }}>
                {angle.questions_to_address.map((q, qi) => (
                  <li key={qi} style={{ fontSize: 11, color: 'var(--dim)', lineHeight: 1.5 }}>
                    {q}
                  </li>
                ))}
              </ul>
            )}

            {/* Action buttons — only on selected card */}
            {isSelected && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button
                  disabled={disabled}
                  onClick={(e) => { e.stopPropagation(); onApprove?.(angle.id) }}
                  style={{ ...BTN, background: 'rgba(34,197,94,.18)', color: '#86efac' }}
                >
                  Approve
                </button>
                <button
                  disabled={disabled}
                  onClick={(e) => { e.stopPropagation(); onAdjust?.(angle.id) }}
                  style={{ ...BTN, background: 'rgba(107,142,255,.15)', color: '#a7c8ff' }}
                >
                  Adjust
                </button>
                <button
                  disabled={disabled}
                  onClick={(e) => { e.stopPropagation(); onOverride?.(angle.id) }}
                  style={{ ...BTN, background: 'rgba(167,139,250,.15)', color: '#d4b4fe' }}
                >
                  Override
                </button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
