import { useEffect, useState } from 'react'
import { useParams, useOutletContext } from 'react-router-dom'
import { AlignLeft, Focus, Minimize2 } from 'lucide-react'
import { documentService } from '@/services/documents'
import { analysisService } from '@/services/analysis'
import { Spinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { SummaryPanel } from './read-mode/SummaryPanel'
import { KeywordsPanel } from './read-mode/KeywordsPanel'
import { RelevancePanel } from './read-mode/RelevancePanel'
import { TimePlanPanel } from './read-mode/TimePlanPanel'
import { RelatedDocsPanel } from './read-mode/RelatedDocsPanel'
import { KnowledgeGraphPanel } from './understand-mode/KnowledgeGraphPanel'
import { QAPanel } from './understand-mode/QAPanel'
import { cn } from '@/utils/cn'

const READ_TABS = ['Tóm tắt', 'Từ khóa', 'Độ phù hợp', 'Kế hoạch đọc', 'Tài liệu liên quan']
const UNDERSTAND_TABS = ['Knowledge Graph', 'Hỏi & Đáp']

export function DocumentPage() {
  const { docId } = useParams()
  const { pendingAction, clearAction, focusMode, setFocusMode } = useOutletContext() ?? {}
  const [doc, setDoc] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [mode, setMode] = useState('read')
  const [activeTab, setActiveTab] = useState(0)
  const [loading, setLoading] = useState(true)
  const [textPanelVisible, setTextPanelVisible] = useState(true)

  useEffect(() => {
    Promise.all([documentService.get(docId), analysisService.getAll(docId)])
      .then(([d, a]) => { setDoc(d); setAnalysis(a) })
      .finally(() => setLoading(false))
  }, [docId])

  useEffect(() => {
    if (!pendingAction) return
    const actionMap = {
      summarize:   () => { setMode('read');       setActiveTab(0) },
      keywords:    () => { setMode('read');       setActiveTab(1) },
      relevance:   () => { setMode('read');       setActiveTab(2) },
      'time-plan': () => { setMode('read');       setActiveTab(3) },
      kg:          () => { setMode('understand'); setActiveTab(0) },
      qa:          () => { setMode('understand'); setActiveTab(1) },
    }
    actionMap[pendingAction]?.()
    clearAction?.()
  }, [pendingAction])

  useEffect(() => {
    const handler = (e) => {
      const tag = e.target.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      if (e.key === 'f' || e.key === 'F') {
        setFocusMode?.((prev) => !prev)
      }
      if (e.key === 'Escape' && focusMode) {
        setFocusMode?.(false)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [focusMode, setFocusMode])

  if (loading) return <div className="flex h-64 items-center justify-center"><Spinner size="lg" /></div>
  if (!doc)    return <div className="p-6 text-[var(--text-muted)]">Tài liệu không tồn tại.</div>

  const tabs = mode === 'read' ? READ_TABS : UNDERSTAND_TABS

  const showTextPanel = textPanelVisible && !focusMode
  const toolsOnlyFocus = focusMode

  return (
    <div className="flex h-full overflow-hidden animate-page-in">
      {/* ── Text panel ──────────────────────────────────── */}
      {showTextPanel && (
        <div
          className={cn(
            'flex flex-col border-r border-[var(--border)] bg-[var(--bg-surface)]',
            'transition-[width] duration-200 ease-in-out shrink-0',
            'w-[42%] xl:w-[45%]',
          )}
        >
          <div className="flex h-10 items-center justify-between px-4 border-b border-[var(--border)] shrink-0">
            <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide">
              Nội dung văn bản
            </span>
            <button
              onClick={() => setTextPanelVisible(false)}
              title="Ẩn văn bản"
              className="rounded p-1 text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]"
            >
              ×
            </button>
          </div>
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="prose-reading text-[var(--text-primary)] max-w-[640px] whitespace-pre-wrap">
              {doc.extracted_text || (
                <span className="text-[var(--text-muted)] italic text-sm">Không có văn bản.</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Tools panel ─────────────────────────────────── */}
      <div
        className={cn(
          'flex flex-col overflow-hidden',
          toolsOnlyFocus ? 'w-full max-w-[720px] mx-auto' : 'flex-1',
        )}
      >
        {/* Doc header */}
        <div className="px-5 py-3 border-b border-[var(--border)] bg-[var(--bg-surface)] shrink-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="font-semibold text-[var(--text-primary)] truncate">{doc.title}</h2>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="text-xs text-[var(--text-muted)] uppercase">{doc.file_type}</span>
                {doc.word_count && <span className="text-xs text-[var(--text-muted)]">{doc.word_count.toLocaleString()} từ</span>}
                {doc.page_count && <span className="text-xs text-[var(--text-muted)]">{doc.page_count} trang</span>}
              </div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {!showTextPanel && (
                <button
                  onClick={() => setTextPanelVisible(true)}
                  title="Hiện văn bản (split view)"
                  className="rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]"
                >
                  <AlignLeft size={15} />
                </button>
              )}
              <button
                onClick={() => setFocusMode?.((prev) => !prev)}
                title={focusMode ? 'Thoát focus mode (Esc)' : 'Focus mode — đọc tập trung (F)'}
                className={cn(
                  'rounded-md p-1.5 hover:bg-[var(--bg-muted)]',
                  focusMode
                    ? 'text-[var(--accent)] bg-[var(--bg-muted)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]',
                )}
              >
                {focusMode ? <Minimize2 size={15} /> : <Focus size={15} />}
              </button>
            </div>
          </div>
        </div>

        {/* Mode toggle */}
        <div className="flex items-center gap-1 px-5 py-2.5 border-b border-[var(--border)] shrink-0">
          <Button
            variant={mode === 'read' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => { setMode('read'); setActiveTab(0) }}
          >
            Đọc thông minh
          </Button>
          <Button
            variant={mode === 'understand' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => { setMode('understand'); setActiveTab(0) }}
          >
            Hiểu sâu
          </Button>
        </div>

        {/* Sub-tabs */}
        <div className="flex gap-1 px-5 py-2 border-b border-[var(--border)] overflow-x-auto shrink-0">
          {tabs.map((tab, i) => (
            <button
              key={tab}
              onClick={() => setActiveTab(i)}
              className={cn(
                'shrink-0 rounded-md px-3 py-1.5 text-sm transition-colors',
                activeTab === i
                  ? 'bg-[var(--bg-muted)] text-[var(--text-primary)] font-medium'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]',
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Panel content */}
        <div className="flex-1 overflow-y-auto p-5">
          {mode === 'read' && (
            <>
              {activeTab === 0 && <SummaryPanel docId={docId} cached={analysis?.summary} onUpdate={(v) => setAnalysis((a) => ({ ...a, summary: v }))} />}
              {activeTab === 1 && <KeywordsPanel docId={docId} cached={analysis?.keywords} onUpdate={(v) => setAnalysis((a) => ({ ...a, keywords: v }))} />}
              {activeTab === 2 && <RelevancePanel docId={docId} cached={analysis?.relevance_score} input={analysis?.relevance_input} onUpdate={(v) => setAnalysis((a) => ({ ...a, ...v }))} />}
              {activeTab === 3 && <TimePlanPanel docId={docId} cached={analysis?.time_plan} input={analysis?.time_plan_input} onUpdate={(v) => setAnalysis((a) => ({ ...a, time_plan: v }))} />}
              {activeTab === 4 && <RelatedDocsPanel docId={docId} />}
            </>
          )}
          {mode === 'understand' && (
            <>
              {activeTab === 0 && <KnowledgeGraphPanel docId={docId} cached={analysis?.kg} onUpdate={(v) => setAnalysis((a) => ({ ...a, kg: v }))} />}
              {activeTab === 1 && <QAPanel docId={docId} />}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
