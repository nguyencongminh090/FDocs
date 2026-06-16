import api, { getAuthToken } from './api'

export const documentService = {
  // POST returns 202 + { job_id }; the chunk/embed pipeline runs server-side.
  // Watch it via streamProgress(job_id, ...).
  create: (payload) =>
    api.post('/documents', payload).then((r) => r.data),

  list: () =>
    api.get('/documents').then((r) => r.data),

  get: (id) =>
    api.get(`/documents/${id}`).then((r) => r.data),

  delete: (id) =>
    api.delete(`/documents/${id}`),

  getSimilarityMap: () =>
    api.get('/library/similarity-map').then((r) => r.data),

  // Streams upload-processing progress over fetch-based SSE (not EventSource, so the
  // JWT can travel in the Authorization header — same approach as qaService.streamAsk).
  // Frames are JSON objects: { status, step, progress, doc_id?, error?, detail? }.
  //   onProgress({ step, progress })  — each processing update (0..100)
  //   onDone({ doc_id })              — terminal success
  //   onError({ error, detail })      — terminal failure (quota/service/server/network/HTTP)
  // Returns a cancel function.
  streamProgress(jobId, { onProgress, onDone, onError }) {
    let cancelled = false

    const run = async () => {
      try {
        const token = getAuthToken()
        const headers = { Accept: 'text/event-stream' }
        if (token) headers['Authorization'] = `Bearer ${token}`

        const response = await fetch(`/api/upload/${jobId}/progress`, { method: 'GET', headers })

        if (!response.ok) {
          let detail = `Lỗi ${response.status}`
          try {
            const body = await response.json()
            if (body?.detail) detail = body.detail
          } catch { /* non-JSON error body */ }
          onError?.({ error: String(response.status), detail })
          return
        }
        if (!response.body) return

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let terminated = false

        while (!cancelled) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            // Ignore keepalive comments (": ...") and blank separators.
            if (!line.startsWith('data: ')) continue
            let frame
            try {
              frame = JSON.parse(line.slice(6).trim())
            } catch {
              continue
            }
            if (frame.status === 'error') {
              terminated = true
              onError?.(frame)
              return
            }
            if (frame.status === 'done') {
              terminated = true
              onProgress?.(frame)
              onDone?.(frame)
              return
            }
            onProgress?.(frame)
          }
        }
        // Stream ended without a terminal frame (server closed early) — surface it
        // so the UI doesn't hang on a spinner forever.
        if (!terminated && !cancelled) {
          onError?.({ error: 'closed', detail: 'Kết nối tiến trình bị đóng sớm.' })
        }
      } catch {
        if (!cancelled) onError?.({ error: 'network', detail: 'Mất kết nối khi theo dõi tiến trình.' })
      }
    }

    run()
    return () => { cancelled = true }
  },
}
