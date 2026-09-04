import { useEffect, useState } from 'react'
import { subscribeToProgress } from '../api/client'
import type { KnowledgeGraph } from '../types'

interface ProgressState {
  done: number
  total: number
  result: KnowledgeGraph | null
  error: string | null
}

export function useJobProgress(jobId: string | null): ProgressState {
  const [state, setState] = useState<ProgressState>({ done: 0, total: 0, result: null, error: null })

  useEffect(() => {
    if (!jobId) return

    setState({ done: 0, total: 0, result: null, error: null })

    const source = subscribeToProgress(jobId, {
      onProgress: (done, total) => setState((prev) => ({ ...prev, done, total })),
      onComplete: (graph) => setState((prev) => ({ ...prev, result: graph })),
      onFailed: (message) => setState((prev) => ({ ...prev, error: message })),
    })

    return () => source.close()
  }, [jobId])

  return state
}
