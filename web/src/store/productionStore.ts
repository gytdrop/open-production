import { create } from 'zustand'
import type { Angle, AuditEntry, DemoRunResult, Production } from '../types/production'
import { reframe, finalize, getStatus } from '../hooks/useProductionApi'

// â”€â”€ Store shape â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

interface ProductionStore {
  // Shared
  productionId: string | null
  production: Production | null
  pollingActive: boolean

  // Flow slice
  intent: { topic: string; audience: string; tone: string }
  angles: Angle[]
  chosenAngleId: string | null
  runResult: DemoRunResult | null
  flowStep: number          // 1â€“7, drives StepIndicator
  flowStatus: string        // inline status message
  flowLoading: boolean

  // Console slice
  auditEntries: AuditEntry[]
  selectedActor: string | null   // null = show all
  activeTab: 'events' | 'proposals' | 'state'
  consoleError: string | null

  setFlowStep(step: number): void
  setIntent(intent: Partial<ProductionStore['intent']>): void
  setProductionId(id: string): void
  loadAngles(): Promise<void>
  finalizeRun(angleId: string): Promise<void>
  pollProduction(): Promise<void>
  setSelectedActor(actor: string | null): void
  setActiveTab(tab: ProductionStore['activeTab']): void
  resetFlow(): void
}

// â”€â”€ Store implementation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

// Generation counter (closure-scoped, per store instance).
// Prevents stale step-animation timers from updating state after a reset.
// Holding it inside the factory closure means each store instance gets its own
// counter, so multiple Zustand mounts cannot stomp each other.
export const useProductionStore = create<ProductionStore>((set, get) => {
  let runGeneration = 0
  return {
  // Shared defaults
  productionId: null,
  production: null,
  pollingActive: false,

  // Flow slice defaults
  intent: { topic: '', audience: '', tone: '' },
  angles: [],
  chosenAngleId: null,
  runResult: null,
  flowStep: 1,
  flowStatus: '',
  flowLoading: false,

  // Console slice defaults
  auditEntries: [],
  selectedActor: null,
  activeTab: 'events',
  consoleError: null,

  // â”€â”€ Actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

  setFlowStep(step: number) {
    set({ flowStep: Math.max(1, Math.min(7, step)) })
  },

  setIntent(partial) {
    set((s) => ({ intent: { ...s.intent, ...partial } }))
  },

  setProductionId(id: string) {
    set({ productionId: id, consoleError: null })
  },

  async loadAngles() {
    const { intent } = get()
    // Capture generation so a reset while fetching does not apply stale results.
    const myGen = ++runGeneration
    set({ flowLoading: true, flowStatus: 'Generating anglesâ€¦', angles: [] })
    try {
      const data = await reframe(intent)
      if (myGen !== runGeneration) return
      set({ angles: data.angles, flowStep: 3, flowStatus: 'Pick an angle to advance.' })
    } catch (err) {
      if (myGen !== runGeneration) return
      set({
        flowStatus: err instanceof Error
          ? `Could not generate angles. Is the server running? (${err.message})`
          : 'Could not generate angles. Is the server running?',
      })
    } finally {
      if (myGen === runGeneration) {
        set({ flowLoading: false })
      }
    }
  },

  async finalizeRun(angleId: string) {
    const { intent } = get()
    // Capture generation so stale timer callbacks can detect a reset/re-run.
    const myGen = ++runGeneration
    set({ flowLoading: true, chosenAngleId: angleId, flowStatus: 'Running multi-agent pipelineâ€¦', flowStep: 3 })
    try {
      const result = await finalize(intent, angleId)

      // Bail out if the user already reset or started a new run while we were waiting.
      if (myGen !== runGeneration) return

      set({
        runResult: result,
        productionId: result.production_id,
        auditEntries: result.audit_entries,
        consoleError: null,
        flowLoading: false, // Turn off spinner so step cards display!
      })

      const delay = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

      set({ flowStep: 3, flowStatus: 'Step 3/7: Visual references & moodboard built âœ“' })
      await delay(1500)
      if (myGen !== runGeneration) return

      set({ flowStep: 4, flowStatus: 'Step 4/7: Setting up character casting & locationsâ€¦' })
      await delay(1500)
      if (myGen !== runGeneration) return

      set({ flowStep: 5, flowStatus: 'Step 5/7: Designing shot plan & camera specificationsâ€¦' })
      await delay(1500)
      if (myGen !== runGeneration) return

      set({ flowStep: 6, flowStatus: 'Step 6/7: Generating assets & assembling timelineâ€¦' })
      await delay(1500)
      if (myGen !== runGeneration) return

      set({
        flowStep: 7,
        flowStatus: 'Done',
      })
    } catch (err) {
      // Only update state if this run is still the current one.
      if (myGen !== runGeneration) return
      set({
        flowStatus: err instanceof Error
          ? `The run did not complete. (${err.message})`
          : 'The run did not complete.',
        flowStep: 2,   // step back so user can retry
        flowLoading: false,
      })
    }
  },

  async pollProduction() {
    const { productionId } = get()
    if (!productionId) return
    // Stop polling if a hard error was already recorded
    if (get().consoleError) return
    try {
      const prod = await getStatus(productionId)
      const existing = get().auditEntries
      const existingIds = new Set(existing.map((e) => e.id))
      const newEntries = prod.audit_trail.filter((e) => !existingIds.has(e.id))
      set({
        production: prod,
        auditEntries: [...existing, ...newEntries],
        consoleError: null,
      })
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      // 404 â†’ production not found; set error so polling stops
      if (msg.includes('404')) {
        set({ consoleError: 'Production not found.' })
      }
      // other network errors â†’ silent, retry next tick
    }
  },

  setSelectedActor(actor) {
    set({ selectedActor: actor })
  },

  setActiveTab(tab) {
    set({ activeTab: tab })
  },

  resetFlow() {
    // Invalidate any in-flight finalizeRun delay sequences.
    runGeneration++
    set({
      intent: { topic: '', audience: '', tone: '' },
      angles: [],
      chosenAngleId: null,
      runResult: null,
      flowStep: 1,
      flowStatus: '',
      flowLoading: false,
      productionId: null,
      production: null,
      consoleError: null,
    })
  },
}})


