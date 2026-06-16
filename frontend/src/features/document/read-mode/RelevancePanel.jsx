import { useState } from 'react'
import { analysisService } from '@/services/analysis'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function RelevancePanel({ docId, cached, input: cachedInput, onUpdate }) {
  const [form, setForm] = useState({ goal: cachedInput?.goal ?? '', keywords: cachedInput?.keywords?.join(', ') ?? '', topic: cachedInput?.topic ?? '' })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(cached ? { score: cached } : null)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const keywords = form.keywords.split(',').map((k) => k.trim()).filter(Boolean)
      const data = await analysisService.relevance(docId, { goal: form.goal, keywords, topic: form.topic })
      setResult(data)
      onUpdate({ relevance_score: data.relevance_score })
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Không thể đánh giá độ phù hợp.')
    } finally {
      setLoading(false)
    }
  }

  const scorePercent = result?.relevance_score != null ? Math.round(result.relevance_score * 100) : null

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold text-[var(--text-primary)]">Đánh giá độ phù hợp</h3>

      <form onSubmit={submit} className="flex flex-col gap-3">
        <div>
          <label className="text-xs font-medium text-[var(--text-muted)] mb-1 block">Mục tiêu của bạn</label>
          <textarea
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
            rows={3}
            placeholder="Ví dụ: Nắm kiến thức về đại số tuyến tính cho học máy"
            value={form.goal}
            onChange={(e) => setForm({ ...form, goal: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="text-xs font-medium text-[var(--text-muted)] mb-1 block">Từ khóa quan tâm (cách nhau bằng dấu phẩy)</label>
          <Input
            placeholder="Linear Algebra, Vectorization, Gradient Descent"
            value={form.keywords}
            onChange={(e) => setForm({ ...form, keywords: e.target.value })}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-[var(--text-muted)] mb-1 block">Chủ đề</label>
          <Input
            placeholder="Machine Learning"
            value={form.topic}
            onChange={(e) => setForm({ ...form, topic: e.target.value })}
            required
          />
        </div>
        <Button type="submit" loading={loading} size="sm">Đánh giá</Button>
      </form>

      {result && (
        <div className="rounded-xl bg-[var(--bg-muted)] p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-[var(--text-primary)]">Điểm phù hợp</span>
            <span className="text-2xl font-bold text-[var(--accent)]">{scorePercent}%</span>
          </div>
          <div className="h-2 rounded-full bg-[var(--border)]">
            <div
              className="h-full rounded-full bg-[var(--accent)] transition-all duration-700"
              style={{ width: `${scorePercent}%` }}
            />
          </div>
          {result.explanation && (
            <p className="text-sm text-[var(--text-muted)]">{result.explanation}</p>
          )}
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}
