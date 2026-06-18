import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileType, Trash2, Plus, LayoutGrid, Network } from 'lucide-react'
import { EmptyDocsArt } from '@/components/illustrations/EmptyArt'
import { documentService } from '@/services/documents'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { LibrarySimilarityMap } from './LibrarySimilarityMap'
import { cn } from '@/utils/cn'

export function LibraryPage() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('grid')
  const [mapData, setMapData] = useState(null)
  const [mapLoading, setMapLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    documentService.list()
      .then(setDocs)
      .finally(() => setLoading(false))
  }, [])

  const switchToMap = async () => {
    setView('map')
    if (mapData) return
    setMapLoading(true)
    try {
      const data = await documentService.getSimilarityMap()
      setMapData(data)
    } finally {
      setMapLoading(false)
    }
  }

  const handleDelete = async (id, e) => {
    e.stopPropagation()
    if (!confirm('Xóa tài liệu này?')) return
    await documentService.delete(id)
    setDocs((prev) => prev.filter((d) => d.id !== id))
    setMapData(null)
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="p-6 animate-page-in">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-[var(--text-primary)]">Library</h1>

        <div className="flex items-center gap-2">
          {docs.length >= 2 && (
            <div className="flex rounded-lg border border-[var(--border)] overflow-hidden">
              <ViewToggleBtn
                active={view === 'grid'}
                onClick={() => setView('grid')}
                title="Dạng lưới"
              >
                <LayoutGrid size={14} />
              </ViewToggleBtn>
              <ViewToggleBtn
                active={view === 'map'}
                onClick={switchToMap}
                title="Bản đồ tương đồng"
              >
                <Network size={14} />
              </ViewToggleBtn>
            </div>
          )}
          <Button onClick={() => navigate('/upload')} size="sm">
            <Plus size={16} /> Upload
          </Button>
        </div>
      </div>

      {docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-[var(--text-muted)] decor-dotgrid">
          <EmptyDocsArt size={120} className="text-[var(--accent)] opacity-80 mb-2 animate-float" />
          <p className="font-display text-lg text-[var(--text-primary)]">Chưa có tài liệu nào</p>
          <p className="text-sm">Upload tài liệu đầu tiên để bắt đầu.</p>
        </div>
      ) : view === 'grid' ? (
        <div className="grid gap-3 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc) => (
            <Card
              key={doc.id}
              className="cursor-pointer hover:shadow-md transition-shadow group"
              onClick={() => navigate(`/document/${doc.id}`)}
            >
              <div className="p-4 flex items-start justify-between gap-3">
                <div className="flex gap-3 min-w-0">
                  <FileType size={20} className="mt-0.5 shrink-0 text-[var(--accent)]" />
                  <div className="min-w-0">
                    <p className="font-medium text-sm text-[var(--text-primary)] truncate">{doc.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge>{doc.file_type.toUpperCase()}</Badge>
                      {doc.word_count && (
                        <span className="text-xs text-[var(--text-muted)]">
                          {(doc.word_count / 1000).toFixed(1)}k từ
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[var(--text-muted)] mt-1">
                      {new Date(doc.created_at).toLocaleDateString('vi-VN')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(doc.id, e)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:text-red-500"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div>
          {mapLoading ? (
            <div className="flex h-64 items-center justify-center">
              <Spinner size="lg" />
            </div>
          ) : mapData ? (
            <LibrarySimilarityMap nodes={mapData.nodes} edges={mapData.edges} />
          ) : null}
        </div>
      )}
    </div>
  )
}

function ViewToggleBtn({ active, onClick, title, children }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={cn(
        'px-2.5 py-1.5 text-sm transition-colors',
        active
          ? 'bg-[var(--accent)] text-[var(--accent-fg)]'
          : 'text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]',
      )}
    >
      {children}
    </button>
  )
}
