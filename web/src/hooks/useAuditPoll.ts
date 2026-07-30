import { useEffect, useRef } from "react"
import { useProductionStore } from "../store/productionStore"

const POLL_INTERVAL_MS = 5_000

/**
 * Starts a 5-second interval polling /api/production/:id/status.
 * Diffs new audit_trail entries against the store and appends only new ones.
 * Stops polling automatically when the production is reported not found (404)
 * so we do not hammer the server after a stale id is loaded.
 * Clears the interval on component unmount.
 * Does nothing when productionId is null.
 */
export function useAuditPoll(productionId: string | null): void {
  const pollProduction = useProductionStore((s) => s.pollProduction)
  const consoleError    = useProductionStore((s) => s.consoleError)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!productionId) return
    // Stop polling once the store records a terminal error (e.g. 404).
    if (consoleError) {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    const tick = () => {
      // Defensive: stop scheduling even if consoleError flipped between ticks.
      if (useProductionStore.getState().consoleError) {
        if (intervalRef.current !== null) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
        return
      }
      void pollProduction()
    }

    // Fire once immediately, then every 5s
    void pollProduction()
    intervalRef.current = setInterval(tick, POLL_INTERVAL_MS)

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [productionId, pollProduction, consoleError])
}
