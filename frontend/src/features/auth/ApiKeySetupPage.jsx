import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ExternalLink, Trash2, ShieldCheck } from 'lucide-react'
import { useGeminiKey } from '@/context/GeminiKeyContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent } from '@/components/ui/Card'

function maskKey(key) {
  if (!key) return ''
  if (key.length <= 8) return '•'.repeat(key.length)
  return `${key.slice(0, 4)}••••••••${key.slice(-4)}`
}

export function ApiKeySetupPage() {
  const { saveKey, clearKey, geminiKey, hasKey } = useGeminiKey()
  const navigate = useNavigate()
  const [key, setKey] = useState(geminiKey)
  const [hadKeyInitially] = useState(hasKey)
  const [saved, setSaved] = useState(false)

  const handleSave = (e) => {
    e.preventDefault()
    const trimmed = key.trim()
    if (!trimmed) return
    saveKey(trimmed)
    setSaved(true)
    // First-time setup: send the user into the app. Changing an existing key keeps
    // them on the settings page with an inline confirmation.
    if (!hadKeyInitially) setTimeout(() => navigate('/library'), 1000)
    else setTimeout(() => setSaved(false), 2000)
  }

  const handleRemove = () => {
    clearKey()
    setKey('')
    setSaved(false)
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-12">
      <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
        {hadKeyInitially ? 'Quản lý Gemini API Key' : 'Cấu hình Gemini API Key'}
      </h2>
      <p className="text-sm text-[var(--text-muted)] mb-6">
        FDocs dùng mô hình Gemini của bạn. Key chỉ lưu trong trình duyệt, không gửi lên server.
      </p>

      {hasKey && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--bg-muted)] px-4 py-3 text-sm">
          <ShieldCheck size={16} className="text-[var(--success)] shrink-0" />
          <span className="text-[var(--text-muted)]">Key hiện tại:</span>
          <code className="font-mono text-[var(--text-primary)]">{maskKey(geminiKey)}</code>
        </div>
      )}

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <Input
              type="password"
              placeholder={hasKey ? 'Nhập key mới để thay thế' : 'AIza...'}
              value={key}
              onChange={(e) => setKey(e.target.value)}
              required
            />
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-xs text-[var(--accent)] hover:underline"
            >
              Lấy Gemini API Key miễn phí <ExternalLink size={12} />
            </a>
            <Button type="submit" className="w-full" disabled={saved}>
              {saved
                ? hadKeyInitially
                  ? '✓ Đã cập nhật key'
                  : '✓ Đã lưu — đang chuyển hướng...'
                : hasKey
                  ? 'Cập nhật Key'
                  : 'Lưu Key'}
            </Button>
          </form>

          {hasKey && (
            <button
              type="button"
              onClick={handleRemove}
              className="mt-4 flex w-full items-center justify-center gap-1.5 text-xs text-[var(--error)] hover:underline"
            >
              <Trash2 size={12} />
              Xoá key khỏi trình duyệt
            </button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
