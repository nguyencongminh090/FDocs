import { cn } from '@/utils/cn'

const variants = {
  primary: 'bg-[var(--accent)] text-[var(--accent-fg)] hover:bg-[var(--accent-hover)]',
  outline: 'border border-[var(--border)] bg-transparent hover:bg-[var(--bg-muted)]',
  ghost: 'bg-transparent hover:bg-[var(--bg-muted)]',
  destructive: 'bg-red-600 text-white hover:bg-red-700',
}

const sizes = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-9 px-4 text-sm',
  lg: 'h-10 px-6 text-base',
  icon: 'h-9 w-9',
}

export function Button({ variant = 'primary', size = 'md', className, disabled, loading, children, ...props }) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
        'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]',
        'active:scale-[0.97] active:transition-transform',
        'hover:-translate-y-px',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:translate-y-0 disabled:scale-100',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}
