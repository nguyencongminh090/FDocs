import { useEffect, useState } from 'react'
import { Navigate, Outlet, NavLink, useParams } from 'react-router-dom'
import { BookOpen, Upload, LogOut, Settings, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useGeminiKey } from '@/context/GeminiKeyContext'
import { ThemeSwitcher } from '@/components/ThemeSwitcher'
import { CommandPalette } from '@/components/CommandPalette'
import { cn } from '@/utils/cn'

function loadCollapsed() {
  try { return localStorage.getItem('sidebar-collapsed') === 'true' } catch { return false }
}

export function AppLayout() {
  const { isAuthenticated, logout, isLoading } = useAuth()
  const { hasKey } = useGeminiKey()
  const [paletteAction, setPaletteAction] = useState(null)
  const [collapsed, setCollapsed] = useState(loadCollapsed)
  const [focusMode, setFocusMode] = useState(false)
  const { docId } = useParams()

  const toggleCollapsed = () =>
    setCollapsed((prev) => {
      const next = !prev
      try { localStorage.setItem('sidebar-collapsed', String(next)) } catch {}
      return next
    })

  useEffect(() => {
    const handler = (e) => {
      if (e.key === '\\' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        toggleCollapsed()
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />

  const sidebarHidden = focusMode
  const sidebarWidth = sidebarHidden ? 'w-0 overflow-hidden border-r-0' : collapsed ? 'w-14' : 'w-60'

  return (
    <div className="flex h-screen bg-[var(--bg-base)] overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col border-r border-[var(--border)] bg-[var(--bg-surface)]',
          'transition-[width] duration-250 ease-in-out shrink-0',
          sidebarWidth,
        )}
      >
        <div className="flex h-14 items-center justify-between px-3 border-b border-[var(--border)] shrink-0">
          {!collapsed && (
            <span className="font-bold text-[var(--text-primary)] select-none">FDocs</span>
          )}
          <button
            onClick={toggleCollapsed}
            title={collapsed ? 'Mở rộng thanh bên (\\)' : 'Thu gọn thanh bên (\\)'}
            className={cn(
              'rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]',
              collapsed && 'mx-auto',
            )}
          >
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        <nav className="flex flex-col gap-1 p-2 flex-1">
          <SidebarLink to="/library" icon={<BookOpen size={16} />} collapsed={collapsed}>
            Library
          </SidebarLink>
          <SidebarLink to="/upload" icon={<Upload size={16} />} collapsed={collapsed}>
            Upload
          </SidebarLink>
        </nav>

        <div className="p-2 border-t border-[var(--border)] flex flex-col gap-1 shrink-0 decor-dotgrid">
          <NavLink
            to="/settings"
            title={collapsed ? (hasKey ? 'Cài đặt' : 'Cài đặt — chưa có Gemini Key') : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
                collapsed && 'justify-center px-0',
                !hasKey
                  ? 'text-amber-600 bg-amber-50 hover:bg-amber-100 font-medium'
                  : isActive
                    ? 'bg-[var(--accent)] text-[var(--accent-fg)] font-medium'
                    : 'text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]',
              )
            }
          >
            <Settings size={16} />
            {!collapsed && (hasKey ? 'Cài đặt' : 'Cài đặt — chưa có key')}
          </NavLink>
          <button
            onClick={logout}
            title="Đăng xuất"
            className={cn(
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[var(--text-muted)]',
              'hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]',
              collapsed && 'justify-center px-0',
            )}
          >
            <LogOut size={16} />
            {!collapsed && 'Đăng xuất'}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--border)] px-4 bg-[var(--bg-surface)]">
          <button
            className="text-xs text-[var(--text-muted)] border border-[var(--border)] rounded-md px-3 py-1.5 hover:bg-[var(--bg-muted)]"
            onClickCapture={(e) => {
              e.preventDefault()
              document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true, bubbles: true }))
            }}
          >
            ⌘K — Lệnh nhanh
          </button>
          <ThemeSwitcher />
        </header>

        <div className="flex-1 overflow-hidden">
          <Outlet
            context={{
              pendingAction: paletteAction,
              clearAction: () => setPaletteAction(null),
              focusMode,
              setFocusMode,
            }}
          />
        </div>
      </main>

      <CommandPalette docId={docId} onAction={setPaletteAction} />
    </div>
  )
}

function SidebarLink({ to, icon, collapsed, children }) {
  return (
    <NavLink
      to={to}
      title={collapsed ? String(children) : undefined}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
          collapsed && 'justify-center px-0',
          isActive
            ? 'bg-[var(--accent)] text-[var(--accent-fg)] font-medium'
            : 'text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)]',
        )
      }
    >
      {icon}
      {!collapsed && children}
    </NavLink>
  )
}
