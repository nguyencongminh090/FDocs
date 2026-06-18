import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { Send, Trash2 } from 'lucide-react'
import { MarkdownLatex } from '@/components/ui/MarkdownLatex'
import { EmptyQAArt } from '@/components/illustrations/EmptyArt'
import { qaService } from '@/services/qa'
import { Button } from '@/components/ui/Button'

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}

export function QAPanel({ docId }) {
  const [history, setHistory] = useState([])
  const [question, setQuestion] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamText, setStreamText] = useState('')
  const [error, setError] = useState('')
  const scrollContainerRef = useRef(null)
  const bottomRef = useRef(null)

  const hasContent = history.length > 0 || streaming || !!error

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'instant' })
  }, [])

  useEffect(() => {
    qaService.history(docId).then(setHistory)
  }, [docId])

  // Issue 2: scroll before paint to prevent flash-to-top on history reload
  useLayoutEffect(() => {
    scrollToBottom()
  }, [history, streamText, scrollToBottom])

  // Issue 3: re-observe inner div when content appears; ResizeObserver fires when KaTeX expands DOM
  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return
    const inner = container.firstElementChild
    if (!inner) return
    const observer = new ResizeObserver(scrollToBottom)
    observer.observe(inner)
    return () => observer.disconnect()
  }, [hasContent, scrollToBottom])

  const handleClear = async () => {
    try {
      await qaService.clearHistory(docId)
      setHistory([])
      setError('')
      setStreamText('')
    } catch {
      setError('Không thể xóa lịch sử. Vui lòng thử lại.')
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    const q = question.trim()
    if (!q || streaming) return
    setQuestion('')
    setStreaming(true)
    setStreamText('')
    setError('')

    const optimisticQ = { id: Date.now(), question: q, answer: null, sources: null, created_at: new Date().toISOString() }
    setHistory((h) => [...h, optimisticQ])

    let fullAnswer = ''
    const cleanup = qaService.streamAsk(
      docId,
      q,
      (token) => {
        fullAnswer += token
        setStreamText(fullAnswer)
      },
      async () => {
        setStreaming(false)
        setStreamText('')
        const updated = await qaService.history(docId)
        setHistory(updated)
        cleanup?.()
      },
      (info) => {
        setError(info?.detail || 'Đã xảy ra lỗi khi trả lời. Vui lòng thử lại.')
      },
    )
  }

  return (
    <div className="flex flex-col h-full gap-0 pt-5 pb-4">
      <div ref={scrollContainerRef} className="flex-1 min-h-0 overflow-y-auto">
        {!hasContent ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-center py-8 px-5 decor-dotgrid">
            <EmptyQAArt size={112} className="text-[var(--accent)] opacity-80 mb-1 animate-float" />
            <p className="font-display text-lg text-[var(--text-primary)]">Chưa có câu hỏi nào</p>
            <p className="text-xs text-[var(--text-muted)] opacity-70">Đặt câu hỏi về tài liệu phía dưới để bắt đầu.</p>
          </div>
        ) : (
          <div className="flex flex-col justify-end min-h-full gap-4 pb-4 px-5">
            {history.length > 0 && !streaming && (
              <div className="flex justify-end pb-2">
                <Button size="sm" variant="ghost" onClick={handleClear}>
                  <Trash2 size={14} className="mr-1.5" />
                  Xóa lịch sử
                </Button>
              </div>
            )}

            {history.map((item) => (
              <div key={item.id} className="flex flex-col gap-2">
                <div className="flex flex-col items-end gap-0.5">
                  <div className="max-w-[80%] rounded-xl rounded-br-sm bg-[var(--accent)] text-[var(--accent-fg)] px-4 py-2 text-sm break-words">
                    {item.question}
                  </div>
                  {item.created_at && (
                    <span className="text-[10px] text-[var(--text-muted)] opacity-60 pr-1">
                      {formatTime(item.created_at)}
                    </span>
                  )}
                </div>
                {item.answer && (
                  <div className="flex flex-col items-start gap-0.5">
                    <div className="max-w-[90%] rounded-xl rounded-bl-sm bg-[var(--bg-muted)] px-4 py-3 text-sm text-[var(--text-primary)] prose-reading leading-relaxed break-words overflow-x-auto">
                      <MarkdownLatex>{item.answer}</MarkdownLatex>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {streaming && streamText && (
              <div className="self-start max-w-[90%] rounded-xl rounded-bl-sm bg-[var(--bg-muted)] px-4 py-3 text-sm text-[var(--text-primary)] prose-reading leading-relaxed break-words overflow-x-auto">
                <MarkdownLatex>{streamText}</MarkdownLatex>
                <span className="inline-block w-1 h-4 bg-[var(--accent)] animate-pulse ml-0.5 align-middle" />
              </div>
            )}

            {error && (
              <div className="self-start max-w-[90%] rounded-xl rounded-bl-sm border border-[var(--error)] bg-[var(--error-bg)] px-4 py-3 text-sm text-[var(--error)] break-words">
                {error}
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <form onSubmit={submit} className="flex gap-2 pt-4 px-5 border-t border-[var(--border)]">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Đặt câu hỏi về tài liệu..."
          disabled={streaming}
          className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] disabled:opacity-50"
        />
        <Button type="submit" size="icon" disabled={!question.trim() || streaming}>
          <Send size={16} />
        </Button>
      </form>
    </div>
  )
}
