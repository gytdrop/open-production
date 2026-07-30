import type { Angle, DemoRunResult, Production } from '../types/production'

// ── Reframe ────────────────────────────────────────────────────────────────

export async function reframe(intent: {
  topic: string
  audience: string
  tone: string
}): Promise<{ angles: Angle[] }> {
  const res = await fetch('/api/reframe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(intent),
  })
  if (!res.ok) throw new Error(`reframe failed: ${res.status}`)
  return res.json() as Promise<{ angles: Angle[] }>
}

// ── Finalize ───────────────────────────────────────────────────────────────

export async function finalize(
  intent: { topic: string; audience: string; tone: string },
  chosenAngleId: string,
): Promise<DemoRunResult> {
  const res = await fetch('/api/finalize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...intent, chosen_angle_id: chosenAngleId }),
  })
  if (!res.ok) throw new Error(`finalize failed: ${res.status}`)
  return res.json() as Promise<DemoRunResult>
}

// ── Status ─────────────────────────────────────────────────────────────────

export async function getStatus(id: string): Promise<Production> {
  const res = await fetch(`/api/production/${encodeURIComponent(id)}/status`)
  if (!res.ok) throw new Error(`getStatus failed: ${res.status}`)
  return res.json() as Promise<Production>
}
