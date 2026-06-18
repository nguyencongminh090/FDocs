import api, { getAuthToken, getResponseLanguageHeader } from './api'

export const qaService = {
  ask: (docId, question) =>
    api.post(`/documents/${docId}/qa`, { question }).then((r) => r.data),

  history: (docId) =>
    api.get(`/documents/${docId}/qa`).then((r) => r.data),

  clearHistory: (docId) =>
    api.delete(`/documents/${docId}/qa`).then((r) => r.data),

  // onError(info) is called for both a non-OK initial response (e.g. 429/502 raised
  // before streaming starts) and an in-band error frame emitted mid-stream
  // (`data: {"error","detail"}`), since once HTTP 200 is committed the backend can
  // only signal failure in-band. onDone always fires afterwards as the cleanup hook.
  streamAsk(docId, question, onToken, onDone, onError) {
    const geminiKey = localStorage.getItem('fdocs-gemini-key')
    let cancelled = false

    const run = async () => {
      try {
        const token = getAuthToken()
        const headers = {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          ...getResponseLanguageHeader(),
        }
        if (token) headers['Authorization'] = `Bearer ${token}`
        if (geminiKey) headers['X-Gemini-Key'] = geminiKey

        const response = await fetch(`/api/documents/${docId}/qa/stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ question }),
        })

        if (!response.ok) {
          let detail = `Lỗi ${response.status}`
          try {
            const body = await response.json()
            if (body?.detail) detail = body.detail
          } catch { /* non-JSON error body */ }
          onError?.({ error: String(response.status), detail })
          onDone?.()
          return
        }
        if (!response.body) {
          onDone?.()
          return
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (!cancelled) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6).trim()
            if (data === '[DONE]') {
              onDone?.()
              return
            }
            let parsed
            try {
              parsed = JSON.parse(data)
            } catch {
              onToken(data)
              continue
            }
            // Error frames are JSON objects with an `error` key; tokens are JSON strings.
            if (parsed && typeof parsed === 'object' && 'error' in parsed) {
              onError?.(parsed)
              onDone?.()
              return
            }
            onToken(parsed)
          }
        }
        onDone?.()
      } catch {
        onError?.({ error: 'network', detail: 'Mất kết nối khi nhận câu trả lời.' })
        onDone?.()
      }
    }

    run()
    return () => { cancelled = true }
  },
}
