import { useEffect, useRef } from 'react'
import { useProductionStore } from '../../store/productionStore'
import type { AuditEntry } from '../../types/production'
import SystemEvent from './SystemEvent'
import AgentMessage from './AgentMessage'
import OptionCards from './OptionCards'
import UserMessage from './UserMessage'
import ThinkingBubble from './ThinkingBubble'
import ReviewerFlag from './ReviewerFlag'

// â”€â”€ Skeleton rows shown while first poll is in flight â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function SkeletonRow({ width }: { width: string }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '10px 0', alignItems: 'center' }}>
      <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--border)', animation: 'skeletonPulse 1.4s ease infinite', flexShrink: 0 }} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ width, height: 10, borderRadius: 4, background: 'var(--border)', animation: 'skeletonPulse 1.4s ease infinite' }} />
        <div style={{ width: '60%', height: 8, borderRadius: 4, background: 'var(--border)', animation: 'skeletonPulse 1.4s ease 0.2s infinite' }} />
      </div>
    </div>
  )
}

// â”€â”€ Actor â†’ avatar colour (P6 spec) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const ACTOR_COLOURS: Record<string, string> = {
  demo_flow:           '#5d6678',
  CreativeReframing:   '#6b8eff',
  ResearchAgent:       '#f0b85d',
  MoodboardAgent:      '#a78bfa',
  ShotDesignerAgent:   '#67e8f9',
  ReviewerAgent:       '#f472b6',
  EditorAgent:         '#22c55e',
  ColoristAgent:       '#fb923c',
  human:               '#22c55e',
  system:              '#22c55e',
}

function actorColour(actor?: string): string {
  if (!actor) return '#8a93a6'
  return ACTOR_COLOURS[actor] ?? '#8a93a6'
}

function actorInitials(actor?: string): string {
  if (!actor) return 'AG'
  return actor
    .replace(/Agent$/, '')
    .split(/(?=[A-Z_])/)
    .filter(Boolean)
    .map((p) => p[0].toUpperCase())
    .slice(0, 2)
    .join('')
    || actor.slice(0, 2).toUpperCase()
}

// â”€â”€ AuditEntry â†’ thread component â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function AuditRow({ entry }: { entry: AuditEntry }) {
  const { action_type, actor, ts, reason, gate_name, decision_status } = entry

  // state_transition, gate_decision, system â†’ SystemEvent
  if (action_type === 'state_transition' || action_type === 'system' || action_type === 'gate_decision') {
    const label = gate_name
      ? `${gate_name} â†’ ${decision_status ?? ''}`
      : (reason ?? action_type.replace(/_/g, ' '))
    return (
      <SystemEvent
        message={label}
        detail={gate_name ? `claim: ${entry.claim_id ?? 'â€”'}` : undefined}
        ts={ts}
        duration={decision_status ? decision_status : undefined}
      />
    )
  }

  // decision by human â†’ UserMessage
  if (action_type === 'decision' && actor === 'human') {
    return <UserMessage text={reason ?? action_type} ts={ts} />
  }

  // everything else â†’ AgentMessage
  return (
    <AgentMessage
      agent={actor}
      initials={actorInitials(actor)}
      avatarColor={actorColour(actor)}
      ts={ts}
      subtitle={reason ? undefined : action_type.replace(/_/g, ' ')}
    >
      {reason && (
        <div style={{ fontSize: 12, color: 'var(--text)', lineHeight: 1.5 }}>{reason}</div>
      )}
    </AgentMessage>
  )
}

// â”€â”€ Static mock thread (shown when no live entries yet) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function MockThread() {
  return (
    <>
      <SystemEvent
        message="âœ“ Shot 7 generation complete"
        detail="shot_7_v3.jsonl"
        ts="14:22:08"
        duration="12.4s Â· review required"
      />

      <div style={{ height: 1, background: 'var(--border)', margin: '4px 0' }} />

      <AgentMessage
        agent="Creative Director"
        initials="CD"
        avatarColor="#3b5bdb"
        ts="14:22:31"
        subtitle="3 options"
      >
        <div style={{ fontSize: 12, color: 'var(--text)', marginBottom: 4 }}>
          The current shot reads too neutral. I see 3 framings that could elevate the tension:
        </div>
        <OptionCards />
      </AgentMessage>

      <UserMessage
        text="Approve B. But can the camera height be exactly 1.0m â€” I want the subject to loom without losing the stair silhouettes."
        ts="14:23:14"
      />

      <AgentMessage
        agent="Shot Designer"
        initials="SD"
        avatarColor="#5a3a10"
        ts=""
        subtitle="thinkingâ€¦ âš¡"
        thinking
      >
        <ThinkingBubble statusText="Resolving camera spec for option Bâ€¦" />
      </AgentMessage>

      <AgentMessage
        agent="Reviewer"
        initials="RV"
        avatarColor="#5a1a38"
        ts="14:23:48"
        subtitle="1 finding"
      >
        <ReviewerFlag />
      </AgentMessage>

      <div style={{ height: 12 }} />
    </>
  )
}

function matchesActor(entryActor?: string, selectedActor?: string): boolean {
  if (!selectedActor) return true
  if (!entryActor) return false
  const entryLower = entryActor.toLowerCase()
  const selectedLower = selectedActor.toLowerCase()

  if (entryLower === selectedLower) return true

  if (selectedLower.includes('producer') && (entryLower.includes('demo_flow') || entryLower.includes('system') || entryLower.includes('producer'))) return true
  if (selectedLower.includes('creative') && (entryLower.includes('creative') || entryLower.includes('reframing') || entryLower.includes('confirm'))) return true
  if (selectedLower.includes('editor') && (entryLower.includes('editor') || entryLower.includes('timeline'))) return true
  if (selectedLower.includes('reviewer') && (entryLower.includes('review') || entryLower.includes('gate') || entryLower.includes('evidence') || entryLower.includes('consistency') || entryLower.includes('publication'))) return true
  if (selectedLower.includes('character') && (entryLower.includes('character') || entryLower.includes('actor'))) return true
  if (selectedLower.includes('env') && (entryLower.includes('env') || entryLower.includes('location'))) return true
  if (selectedLower.includes('shot') && (entryLower.includes('shot') || entryLower.includes('camera') || entryLower.includes('lighting'))) return true
  if (selectedLower.includes('storyboard') && entryLower.includes('story')) return true

  return entryLower.includes(selectedLower) || selectedLower.includes(entryLower)
}

// â”€â”€ ConversationThread â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function ConversationThread() {
  const auditEntries    = useProductionStore((s) => s.auditEntries)
  const selectedActor   = useProductionStore((s) => s.selectedActor)
  const setSelectedActor = useProductionStore((s) => s.setSelectedActor)
  const productionId    = useProductionStore((s) => s.productionId)

  const visible = selectedActor
    ? auditEntries.filter((e) => matchesActor(e.actor, selectedActor))
    : auditEntries

  const hasLiveData  = auditEntries.length > 0
  const isLoading    = !!productionId && !hasLiveData

  const scrollRef    = useRef<HTMLDivElement>(null)
  const prevCountRef = useRef(0)

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80
    if (atBottom && auditEntries.length > prevCountRef.current) {
      el.scrollTop = el.scrollHeight
    }
    prevCountRef.current = auditEntries.length
  }, [auditEntries.length])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      {/* Top bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 16px',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--purple)', letterSpacing: '0.08em' }}>
          CONVERSATION
        </span>
        {selectedActor ? (
          <button
            onClick={() => setSelectedActor(null)}
            style={{
              fontSize: 10,
              color: 'var(--accent)',
              background: 'rgba(107,142,255,.12)',
              border: '1px solid var(--accent)',
              borderRadius: 4,
              padding: '2px 8px',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            filter: {selectedActor} âœ• (click to clear)
          </button>
        ) : (
          <button
            style={{
              fontSize: 10,
              color: 'var(--muted)',
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: 4,
              padding: '2px 8px',
              cursor: 'default',
            }}
          >
            filter â–¾ all agents
          </button>
        )}
      </div>

      {/* Scrollable message area */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '0 16px' }}>
        {isLoading ? (
          <>
            <SkeletonRow width="45%" />
            <SkeletonRow width="70%" />
            <SkeletonRow width="55%" />
          </>
        ) : hasLiveData ? (
          visible.length > 0 ? (
            visible.map((entry, i) => (
              <div key={(entry.id || `entry-${i}`) + `-${i}`} className="anim-fade-in">
                <AuditRow entry={entry} />
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--muted)' }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
                No events recorded by {selectedActor}
              </p>
              <p style={{ fontSize: 11, color: 'var(--dim)', marginBottom: 14 }}>
                This agent is on standby. No audit events match this filter for the current run.
              </p>
              <button
                onClick={() => setSelectedActor(null)}
                style={{
                  background: 'rgba(107,142,255,.15)',
                  border: '1px solid var(--accent)',
                  borderRadius: 6,
                  padding: '6px 14px',
                  fontSize: 11,
                  fontWeight: 600,
                  color: 'var(--accent)',
                  cursor: 'pointer',
                }}
              >
                â† Show all crew events ({auditEntries.length} events)
              </button>
            </div>
          )
        ) : (
          <MockThread />
        )}
      </div>
    </div>
  )
}

