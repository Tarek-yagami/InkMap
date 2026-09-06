import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import type { KnowledgeGraph } from '../types'
import { useJobProgress } from './useJobProgress'

// Mocks the API client boundary (not a fake EventSource) so the test
// controls exactly which SSE event fires and when, and asserts on the
// hook's own state transitions - the part actually worth unit testing,
// since api/client.ts itself is thin EventSource plumbing.
vi.mock('../api/client')

const mockedSubscribe = vi.mocked(client.subscribeToProgress)

describe('useJobProgress', () => {
  beforeEach(() => {
    mockedSubscribe.mockReset()
  })

  it('starts at zero progress with no result or error', () => {
    mockedSubscribe.mockReturnValue({ close: vi.fn() } as unknown as EventSource)
    const { result } = renderHook(() => useJobProgress('job-1'))
    expect(result.current).toEqual({ done: 0, total: 0, result: null, error: null })
  })

  it('updates done/total as progress events arrive', () => {
    mockedSubscribe.mockReturnValue({ close: vi.fn() } as unknown as EventSource)
    const { result } = renderHook(() => useJobProgress('job-1'))
    const handlers = mockedSubscribe.mock.calls[0][1]

    act(() => handlers.onProgress(3, 10))
    expect(result.current.done).toBe(3)
    expect(result.current.total).toBe(10)
  })

  it('stores the graph on completion', () => {
    mockedSubscribe.mockReturnValue({ close: vi.fn() } as unknown as EventSource)
    const { result } = renderHook(() => useJobProgress('job-1'))
    const handlers = mockedSubscribe.mock.calls[0][1]
    const graph: KnowledgeGraph = { nodes: [{ name: 'Transformer', type: 'Technology' }], edges: [] }

    act(() => handlers.onComplete(graph))
    expect(result.current.result).toEqual(graph)
  })

  it('stores the error message on failure', () => {
    mockedSubscribe.mockReturnValue({ close: vi.fn() } as unknown as EventSource)
    const { result } = renderHook(() => useJobProgress('job-1'))
    const handlers = mockedSubscribe.mock.calls[0][1]

    act(() => handlers.onFailed('rate limited'))
    expect(result.current.error).toBe('rate limited')
  })

  it('closes the previous subscription when the job id changes', () => {
    const closeFirst = vi.fn()
    const closeSecond = vi.fn()
    mockedSubscribe.mockReturnValueOnce({ close: closeFirst } as unknown as EventSource)
    mockedSubscribe.mockReturnValueOnce({ close: closeSecond } as unknown as EventSource)

    const { rerender, unmount } = renderHook(({ jobId }) => useJobProgress(jobId), {
      initialProps: { jobId: 'job-1' as string | null },
    })
    rerender({ jobId: 'job-2' })
    expect(closeFirst).toHaveBeenCalledTimes(1)

    unmount()
    expect(closeSecond).toHaveBeenCalledTimes(1)
  })

  it('does not subscribe when there is no job id', () => {
    renderHook(() => useJobProgress(null))
    expect(mockedSubscribe).not.toHaveBeenCalled()
  })
})
