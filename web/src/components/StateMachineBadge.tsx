import type { ProductionState } from '@/types/production'

interface Props {
  state: ProductionState
}

const STATE_STYLES: Record<ProductionState, { bg: string; color: string }> = {
  DRAFT:         { bg: 'rgba(255,255,255,0.06)',  color: '#7a8499' },
  BRIEFED:       { bg: 'rgba(91,127,255,0.15)',   color: '#7a9bff' },
  IN_PRODUCTION: { bg: 'rgba(245,166,35,0.15)',   color: '#ffc461' },
  IN_REVIEW:     { bg: 'rgba(157,126,245,0.15)',  color: '#b89ef8' },
  APPROVED:      { bg: 'rgba(45,206,122,0.14)',   color: '#5aeaa0' },
  PUBLISHED:     { bg: 'rgba(77,208,225,0.14)',   color: '#80deea' },
}

export default function StateMachineBadge({ state }: Props) {
  const { bg, color } = STATE_STYLES[state] ?? STATE_STYLES.DRAFT

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 9px',
        borderRadius: 'var(--radius-sm)',
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        background: bg,
        color,
      }}
    >
      {state.replace(/_/g, ' ')}
    </span>
  )
}
