import { useState } from 'react'
import { analysisService } from '@/services/analysis'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Calendar } from 'lucide-react'

export function TimePlanPanel({ docId, cached, input: cachedInput, onUpdate }) {
  const [form, setForm] = useState({
    start_date: cachedInput?.start_date ?? '',
    deadline: cachedInput?.deadline ?? '',
    hours_per_day: cachedInput?.hours_per_day ?? 2,
  })
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState(cached ?? null)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await analysisService.timePlan(docId, { ...form, hours_per_day: Number(form.hours_per_day) })
      setPlan(data.time_plan)
      onUpdate(data.time_plan)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Không thể tạo kế hoạch đọc.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h3 className="font-semibold text-[var(--text-primary)]">Kế hoạch đọc</h3>

      <form onSubmit={submit} className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-[var(--text-muted)] mb-1 block">Ngày bắt đầu</label>
          <Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required />
        </div>
        <div>
          <label className="text-xs font-medium text-[var(--text-muted)] mb-1 block">Deadline</label>
          <Input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} required />
        </div>
        <div className="col-span-2">
          <label className="text-xs font-medium text-[var(--text-muted)] mb-1 block">Số giờ/ngày có thể đọc</label>
          <Input type="number" min="0.5" max="12" step="0.5" value={form.hours_per_day} onChange={(e) => setForm({ ...form, hours_per_day: e.target.value })} required />
        </div>
        <Button type="submit" loading={loading} className="col-span-2" size="sm">Tạo kế hoạch</Button>
      </form>

      {loading && (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-[var(--bg-muted)] animate-pulse" />
          ))}
        </div>
      )}

      {!loading && plan && (
        <div className="flex flex-col gap-2">
          {plan.map((day, i) => (
            <div key={i} className="rounded-lg border border-[var(--border)] bg-[var(--bg-surface)] p-3">
              <div className="flex items-center gap-2 mb-2">
                <Calendar size={14} className="text-[var(--accent)]" />
                <span className="text-sm font-medium text-[var(--text-primary)]">{day.date}</span>
              </div>
              <ul className="flex flex-col gap-1">
                {day.sessions?.map((s, j) => (
                  <li key={j} className="flex items-center justify-between text-xs text-[var(--text-muted)]">
                    <span>{s.title}</span>
                    <span>{s.estimated_minutes} phút</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}
