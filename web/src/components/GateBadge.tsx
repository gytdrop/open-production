interface Props {
  status: string
}

type StatusStyle = { bg: string; color: string }

const STATUS_STYLES: Record<string, StatusStyle> = {
  accepted:               { bg: 'rgba(45,206,122,0.12)',  color: '#5aeaa0' },
  rejected:               { bg: 'rgba(240,98,146,0.12)',  color: '#f48fb1' },
  contradiction_detected: { bg: 'rgba(245,166,35,0.12)',  color: '#ffc461' },
  publish_ok:             { bg: 'rgba(45,206,122,0.12)',  color: '#5aeaa0' },
  publish_rejected:       { bg: 'rgba(240,98,146,0.12)',  color: '#f48fb1' },
  contract_passed:        { bg: 'rgba(45,206,122,0.12)',  color: '#5aeaa0' },
  contract_violated:      { bg: 'rgba(240,98,146,0.12)',  color: '#f48fb1' },
  gate_decision:          { bg: 'rgba(91,127,255,0.12)',  color: '#7a9bff' },
  decision:               { bg: 'rgba(157,126,245,0.12)', color: '#b89ef8' },
  system:                 { bg: 'rgba(255,255,255,0.06)', color: '#7a8499' },
}

const FALLBACK: StatusStyle = { bg: 'rgba(255,255,255,0.06)', color: '#7a8499' }

export default function GateBadge({ status }: Props) {
  const { bg, color } = STATUS_STYLES[status] ?? FALLBACK

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 'var(--radius-sm)',
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: '0.04em',
        background: bg,
        color,
      }}
    >
      {status.replace(/_/g, ' ')}
    </span>
  )
}
