import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock './api' để không kéo axios + interceptor thật vào test
vi.mock('./api', () => ({
  default: {},
  getAuthToken: () => 'fake-jwt-token',
}))

import { documentService } from './documents'

/** Fake fetch trả về SSE body theo từng `chunks` (mô phỏng ranh giới chunk). */
function mockFetchSSE(chunks, { ok = true, status = ok ? 200 : 404, detail } = {}) {
  const encoder = new TextEncoder()
  let i = 0
  const reader = {
    read: async () => {
      if (i >= chunks.length) return { done: true, value: undefined }
      return { done: false, value: encoder.encode(chunks[i++]) }
    },
  }
  return vi.fn(async () => ({
    ok,
    status,
    body: ok ? { getReader: () => reader } : null,
    json: async () => ({ detail }),
  }))
}

/** Chạy streamProgress, thu mọi event (progress/done/error) theo thứ tự, resolve khi terminal. */
function collect(jobId, chunks, opts) {
  return new Promise((resolve) => {
    const events = []
    global.fetch = mockFetchSSE(chunks, opts)
    documentService.streamProgress(jobId, {
      onProgress: (f) => events.push({ type: 'progress', f }),
      onDone: (f) => { events.push({ type: 'done', f }); resolve(events) },
      onError: (f) => { events.push({ type: 'error', f }); resolve(events) },
    })
  })
}

beforeEach(() => {
  localStorage.setItem('fdocs-gemini-key', 'test-key')
})

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('documentService.streamProgress', () => {
  it('emits each progress frame then a terminal done carrying doc_id', async () => {
    const events = await collect('job1', [
      'data: {"status":"processing","step":"chunking","progress":5}\n\n',
      'data: {"status":"processing","step":"embedding","progress":50}\n\n',
      'data: {"status":"done","step":"done","progress":100,"doc_id":"doc-9"}\n\n',
    ])
    expect(events.filter((e) => e.type === 'progress').map((e) => e.f.progress)).toEqual([5, 50, 100])
    const done = events.find((e) => e.type === 'done')
    expect(done.f.doc_id).toBe('doc-9')
    // No error on a clean run.
    expect(events.some((e) => e.type === 'error')).toBe(false)
  })

  it('reassembles a frame split across stream chunk boundaries', async () => {
    const events = await collect('job1', [
      'data: {"status":"proce',
      'ssing","step":"embedding","progress":42}\n\n',
      'data: {"status":"done","step":"done","progress":100,"doc_id":"d1"}\n\n',
    ])
    expect(events[0]).toEqual({ type: 'progress', f: { status: 'processing', step: 'embedding', progress: 42 } })
  })

  it('routes an error frame to onError and does not call onDone', async () => {
    const events = await collect('job1', [
      'data: {"status":"processing","step":"embedding","progress":30}\n\n',
      'data: {"status":"error","error":"quota","detail":"Hết quota"}\n\n',
    ])
    const err = events.find((e) => e.type === 'error')
    expect(err.f).toEqual({ status: 'error', error: 'quota', detail: 'Hết quota' })
    expect(events.some((e) => e.type === 'done')).toBe(false)
  })

  it('ignores keepalive comment lines', async () => {
    const events = await collect('job1', [
      ': keepalive\n\n',
      'data: {"status":"done","step":"done","progress":100,"doc_id":"d2"}\n\n',
    ])
    expect(events.filter((e) => e.type === 'progress')).toHaveLength(1)
    expect(events.find((e) => e.type === 'done').f.doc_id).toBe('d2')
  })

  it('surfaces a non-ok response detail via onError', async () => {
    const events = await collect('jobX', [], { ok: false, status: 404, detail: 'Upload job not found' })
    expect(events).toEqual([{ type: 'error', f: { error: '404', detail: 'Upload job not found' } }])
  })

  it('reports a premature stream close as an error', async () => {
    const events = await collect('job1', [
      'data: {"status":"processing","step":"embedding","progress":20}\n\n',
    ])
    const err = events.find((e) => e.type === 'error')
    expect(err.f.error).toBe('closed')
  })

  it('sends the Authorization header and targets the progress endpoint', async () => {
    const fetchMock = mockFetchSSE(['data: {"status":"done","step":"done","progress":100,"doc_id":"d"}\n\n'])
    global.fetch = fetchMock
    await new Promise((resolve) => {
      documentService.streamProgress('job42', { onDone: resolve, onError: resolve })
    })
    const [url, opts] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/upload/job42/progress')
    expect(opts.method).toBe('GET')
    expect(opts.headers['Authorization']).toBe('Bearer fake-jwt-token')
  })

  it('returns a cancel function', () => {
    global.fetch = mockFetchSSE(['data: {"status":"done","step":"done","progress":100}\n\n'])
    const cancel = documentService.streamProgress('j', { onDone: () => {} })
    expect(typeof cancel).toBe('function')
    cancel()
  })
})
