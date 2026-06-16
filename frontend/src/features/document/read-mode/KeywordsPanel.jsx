import { useState } from 'react'
import { analysisService } from '@/services/analysis'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

const SKELETON_WIDTHS = [72, 88, 64, 96, 80, 68, 92, 76, 84, 60, 88, 70]

export function KeywordsPanel({ docId, cached, onUpdate }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await analysisService.keywords(docId)
      onUpdate(data.keywords)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Không thể trích xuất từ khóa.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-[var(--text-primary)]">Từ khóa & Khái niệm</h3>
        <Button size="sm" variant="outline" onClick={generate} loading={loading}>
          {cached ? 'Trích xuất lại' : 'Trích xuất'}
        </Button>
      </div>

      {loading && (
        <div className="flex flex-wrap gap-2">
          {SKELETON_WIDTHS.map((w, i) => (
            <div key={i} className="skeleton h-6 rounded-full" style={{ width: `${w}px` }} />
          ))}
        </div>
      )}

      {!loading && cached && (
        <div className="flex flex-wrap gap-2">
          {cached.map((kw, i) => (
            <Badge
              key={kw}
              className="animate-tag-in text-sm py-1 px-3"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              {kw}
            </Badge>
          ))}
        </div>
      )}

      {!loading && !cached && (
        <p className="text-sm text-[var(--text-muted)]">Nhấn "Trích xuất" để lấy từ khóa.</p>
      )}

      {error && <p className="text-sm" style={{ color: 'var(--error)' }}>{error}</p>}
    </div>
  )
}
