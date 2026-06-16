import { useState } from 'react'
import { analysisService } from '@/services/analysis'
import { Button } from '@/components/ui/Button'

const SKELETON_WIDTHS = ['92%', '85%', '78%', '88%', '72%', '60%']

export function SummaryPanel({ docId, cached, onUpdate }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await analysisService.summarize(docId)
      onUpdate(data.summary)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Không thể tạo tóm tắt.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[var(--text-primary)]">Tóm tắt</h3>
        <Button size="sm" variant="outline" onClick={generate} loading={loading}>
          {cached ? 'Tạo lại' : 'Tạo tóm tắt'}
        </Button>
      </div>

      {loading && (
        <div className="space-y-2.5">
          {SKELETON_WIDTHS.map((w, i) => (
            <div key={i} className="skeleton h-3.5" style={{ width: w }} />
          ))}
        </div>
      )}

      {!loading && cached && (
        <div className="prose-reading rounded-xl bg-[var(--bg-muted)] p-5 text-[var(--text-primary)] animate-page-in">
          {cached}
        </div>
      )}

      {!loading && !cached && (
        <p className="text-sm text-[var(--text-muted)]">Nhấn "Tạo tóm tắt" để phân tích tài liệu.</p>
      )}

      {error && <p className="text-sm" style={{ color: 'var(--error)' }}>{error}</p>}
    </div>
  )
}
