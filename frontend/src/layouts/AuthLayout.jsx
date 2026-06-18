import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ThemeSwitcher } from '@/components/ThemeSwitcher'
import { usePointerSpotlight } from '@/hooks/usePointerSpotlight'

export function AuthLayout() {
  const { isAuthenticated } = useAuth()
  const spotlightRef = usePointerSpotlight()
  if (isAuthenticated) return <Navigate to="/library" replace />

  return (
    <div ref={spotlightRef} className="min-h-screen flex flex-col bg-[var(--bg-base)] decor-dotgrid decor-spotlight">
      <div className="flex justify-end p-4">
        <ThemeSwitcher />
      </div>
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center">
            <h1 className="font-display text-3xl font-bold text-[var(--text-primary)]">FDocs</h1>
            <p className="font-display mt-1 text-sm text-[var(--text-muted)]">Đọc tài liệu học thuật thông minh hơn</p>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
