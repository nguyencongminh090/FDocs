import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Command } from 'cmdk'

export function CommandPalette({ docId, onAction }) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const down = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  if (!open) return null

  const handleSelect = (action) => {
    setOpen(false)
    onAction?.(action)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      <div className="fixed inset-0 bg-black/40" onClick={() => setOpen(false)} />
      <div className="relative w-full max-w-lg rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] shadow-2xl overflow-hidden">
        <Command>
          <div className="border-b border-[var(--border)] px-4 py-3">
            <Command.Input
              placeholder="Gõ lệnh hoặc tìm kiếm..."
              className="w-full bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] outline-none"
              autoFocus
            />
          </div>
          <Command.List className="max-h-64 overflow-y-auto py-2">
            <Command.Empty className="py-6 text-center text-sm text-[var(--text-muted)]">
              Không tìm thấy lệnh
            </Command.Empty>

            {docId && (
              <Command.Group heading={<span className="px-4 text-xs text-[var(--text-muted)] font-medium">Phân tích tài liệu</span>}>
                <PaletteItem onSelect={() => handleSelect('summarize')}>Tóm tắt tài liệu</PaletteItem>
                <PaletteItem onSelect={() => handleSelect('keywords')}>Trích xuất từ khóa</PaletteItem>
                <PaletteItem onSelect={() => handleSelect('relevance')}>Đánh giá độ phù hợp</PaletteItem>
                <PaletteItem onSelect={() => handleSelect('time-plan')}>Lên kế hoạch đọc</PaletteItem>
                <PaletteItem onSelect={() => handleSelect('kg')}>Tạo Knowledge Graph</PaletteItem>
                <PaletteItem onSelect={() => handleSelect('qa')}>Đặt câu hỏi (Q&A)</PaletteItem>
              </Command.Group>
            )}

            <Command.Group heading={<span className="px-4 text-xs text-[var(--text-muted)] font-medium">Điều hướng</span>}>
              <PaletteItem onSelect={() => { setOpen(false); navigate('/library') }}>Đến Library</PaletteItem>
              <PaletteItem onSelect={() => { setOpen(false); navigate('/upload') }}>Upload tài liệu mới</PaletteItem>
              <PaletteItem onSelect={() => { setOpen(false); navigate('/settings/api-key') }}>Cài đặt Gemini API Key</PaletteItem>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  )
}

function PaletteItem({ children, onSelect }) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-3 px-4 py-2 text-sm text-[var(--text-primary)] hover:bg-[var(--bg-muted)] aria-selected:bg-[var(--bg-muted)]"
    >
      {children}
    </Command.Item>
  )
}
