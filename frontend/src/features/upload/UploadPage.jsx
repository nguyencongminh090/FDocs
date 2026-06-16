import { useRef, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText } from 'lucide-react'
import { parsePdf } from '@/utils/pdf-parser'
import { parseDocx } from '@/utils/docx-parser'
import { documentService } from '@/services/documents'
import { useGeminiKey } from '@/context/GeminiKeyContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

// Mirrors backend MAX_EXTRACTED_TEXT_CHARS — reject oversized docs client-side before
// a wasted parse→upload round-trip that the server would 422.
const MAX_EXTRACTED_TEXT_CHARS = 1_000_000

// Server-reported pipeline steps → user-facing label.
const STEP_LABELS = {
  chunking: 'Đang chia nhỏ tài liệu...',
  embedding: 'Đang tạo embeddings...',
  saving: 'Đang lưu tài liệu...',
  done: 'Hoàn tất',
}

export function UploadPage() {
  const { hasKey } = useGeminiKey()
  const navigate = useNavigate()
  const inputRef = useRef(null)
  const cancelRef = useRef(null)
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  // idle → parsing (local) → processing (server SSE) → done
  const [phase, setPhase] = useState('idle')
  const [statusLabel, setStatusLabel] = useState('')
  const [percent, setPercent] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => () => cancelRef.current?.(), [])

  const handleFile = (f) => {
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx'].includes(ext)) {
      setError('Chỉ hỗ trợ PDF hoặc DOCX')
      return
    }
    setFile(f)
    setTitle(f.name.replace(/\.[^.]+$/, ''))
    setError('')
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || phase !== 'idle') return
    setError('')
    setPercent(0)

    try {
      setPhase('parsing')
      setStatusLabel('Đang đọc file...')
      const ext = file.name.split('.').pop().toLowerCase()
      const parsed = ext === 'pdf' ? await parsePdf(file) : await parseDocx(file)

      if (parsed.extractedText.length > MAX_EXTRACTED_TEXT_CHARS) {
        setPhase('idle')
        setError(
          `Tài liệu quá lớn (${parsed.extractedText.length.toLocaleString('vi-VN')} ký tự). ` +
          `Giới hạn ${MAX_EXTRACTED_TEXT_CHARS.toLocaleString('vi-VN')} ký tự — hãy tách nhỏ tài liệu.`,
        )
        return
      }

      setPhase('processing')
      setStatusLabel('Đang khởi tạo xử lý...')
      const { job_id } = await documentService.create({
        title: title.trim() || file.name,
        file_type: ext,
        extracted_text: parsed.extractedText,
        word_count: parsed.wordCount,
        page_count: parsed.pageCount ?? null,
      })

      cancelRef.current = documentService.streamProgress(job_id, {
        onProgress: ({ step, progress }) => {
          if (typeof progress === 'number') setPercent(progress)
          if (step && STEP_LABELS[step]) setStatusLabel(STEP_LABELS[step])
        },
        onDone: ({ doc_id }) => {
          setPhase('done')
          setPercent(100)
          if (doc_id) setTimeout(() => navigate(`/document/${doc_id}`), 600)
          else setError('Xử lý xong nhưng không nhận được mã tài liệu.')
        },
        onError: ({ detail }) => {
          setPhase('idle')
          setError(detail || 'Xử lý tài liệu thất bại. Thử lại sau.')
        },
      })
    } catch (err) {
      setPhase('idle')
      setError(err.response?.data?.detail ?? 'Upload thất bại. Kiểm tra Gemini Key.')
    }
  }

  if (!hasKey) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-4 text-[var(--text-muted)]">
        <p className="text-sm">Cần có Gemini API Key để tạo embeddings khi upload.</p>
        <Button onClick={() => navigate('/settings/api-key')} variant="outline" size="sm">
          Cấu hình Key
        </Button>
      </div>
    )
  }

  const busy = phase !== 'idle' && phase !== 'done'
  const barWidth = phase === 'processing' ? percent : phase === 'parsing' ? 8 : 0

  return (
    <div className="max-w-xl mx-auto px-4 py-10">
      <h1 className="text-xl font-semibold text-[var(--text-primary)] mb-6">Upload tài liệu</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-[var(--border)] bg-[var(--bg-surface)] py-10 cursor-pointer hover:border-[var(--accent)] hover:bg-[var(--bg-muted)] transition-colors"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          />
          {file ? (
            <>
              <FileText size={32} className="text-[var(--accent)]" />
              <p className="text-sm font-medium text-[var(--text-primary)]">{file.name}</p>
              <p className="text-xs text-[var(--text-muted)]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </>
          ) : (
            <>
              <Upload size={32} className="text-[var(--text-muted)]" />
              <p className="text-sm text-[var(--text-muted)]">Kéo file vào đây hoặc click để chọn</p>
              <p className="text-xs text-[var(--text-muted)]">PDF, DOCX</p>
            </>
          )}
        </div>

        {file && (
          <Input
            placeholder="Tên tài liệu"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        )}

        {error && <p className="text-sm text-[var(--error)]">{error}</p>}

        {busy && (
          <div className="rounded-lg bg-[var(--bg-muted)] px-4 py-3 text-sm text-[var(--text-muted)]">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent shrink-0" />
                {statusLabel}
              </div>
              {phase === 'processing' && (
                <span className="text-xs font-medium text-[var(--text-primary)] shrink-0">{percent}%</span>
              )}
            </div>
            <div className="mt-2 h-1 rounded-full bg-[var(--border)] overflow-hidden">
              <div
                className="h-full bg-[var(--accent)] transition-all duration-500"
                style={{ width: `${barWidth}%` }}
              />
            </div>
          </div>
        )}

        {phase === 'done' && (
          <p className="text-sm text-[var(--success)] font-medium">✓ Hoàn thành — đang chuyển hướng...</p>
        )}

        <Button type="submit" disabled={!file || busy} loading={busy}>
          Xử lý tài liệu
        </Button>
      </form>
    </div>
  )
}
