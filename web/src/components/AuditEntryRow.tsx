import type { AuditEntry } from '@/types/production'
import GateBadge from './GateBadge'

interface Props {
  entry: AuditEntry
}

function formatTs(ts: string): string {
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
  }
}

export default function AuditEntryRow({ entry }: Props) {
  const statusKey = entry.decision_status ?? entry.action_type

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: 10,
        padding: '6px 12px',
        borderBottom: '1px solid var(--border)',
        fontSize: 12,
        lineHeight: 1.5,
      }}
    >
      {/* Timestamp */}
      <span
        style={{
          color: 'var(--dim)',
          fontVariantNumeric: 'tabular-nums',
          flexShrink: 0,
          fontSize: 10,
          letterSpacing: '0.01em',
        }}
      >
        {formatTs(entry.ts)}
      </span>

      {/* Actor */}
      <span
        style={{
          color: 'var(--accent2)',
          fontWeight: 600,
          flexShrink: 0,
          minWidth: 90,
          fontSize: 11,
        }}
      >
        {entry.actor}
      </span>

      {/* Gate / claim label */}
      {entry.gate_name && (
        <span style={{ color: 'var(--muted)', flexShrink: 0, fontSize: 11 }}>{entry.gate_name}</span>
      )}

      {/* Status badge */}
      <GateBadge status={statusKey} />

      {/* Reason */}
      {entry.reason && (
        <span
          style={{
            color: 'var(--muted)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            fontSize: 11,
          }}
        >
          {entry.reason}
        </span>
      )}
    </div>
  )
}
