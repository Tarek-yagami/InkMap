import type { JobStatus, KnowledgeGraph, ProviderSummary } from '../types'

const API_BASE = '/api'

export async function fetchProviders(): Promise<ProviderSummary[]> {
  const res = await fetch(`${API_BASE}/providers`)
  if (!res.ok) throw new Error('Failed to load providers.')
  return res.json()
}

export async function startJob(formData: FormData): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/jobs`, { method: 'POST', body: formData })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? 'Failed to start extraction.')
  }
  return res.json()
}

export async function fetchJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`)
  if (!res.ok) throw new Error('Failed to fetch job status.')
  return res.json()
}

export interface ProgressHandlers {
  onProgress: (done: number, total: number) => void
  onComplete: (graph: KnowledgeGraph) => void
  onFailed: (message: string) => void
}

export function subscribeToProgress(jobId: string, handlers: ProgressHandlers): EventSource {
  const source = new EventSource(`${API_BASE}/jobs/${jobId}/stream`)

  source.addEventListener('progress', (event) => {
    const data = JSON.parse((event as MessageEvent).data)
    handlers.onProgress(data.done, data.total)
  })

  source.addEventListener('complete', (event) => {
    const graph = JSON.parse((event as MessageEvent).data) as KnowledgeGraph
    handlers.onComplete(graph)
    source.close()
  })

  // The server's own terminal failure event, distinct from EventSource's
  // native "error" (connection-level failure, handled below).
  source.addEventListener('failed', (event) => {
    const data = JSON.parse((event as MessageEvent).data)
    handlers.onFailed(data.message)
    source.close()
  })

  source.onerror = () => {
    // Fires on a genuine connection problem, not on a server-sent "failed"
    // event (that has its own listener above and closes the source itself
    // before this could fire for the same reason).
    if (source.readyState === EventSource.CLOSED) return
    handlers.onFailed('Lost connection to the server.')
    source.close()
  }

  return source
}
