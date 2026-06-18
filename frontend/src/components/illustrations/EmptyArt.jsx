/**
 * Lightweight monochrome line-art for empty states.
 * Stroke uses currentColor (set color via the parent, e.g. text-[var(--accent)]).
 * A small secondary spark uses --accent-2 for a touch of life. Static (no motion).
 */

export function EmptyDocsArt({ size = 120, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {/* open book */}
      <path d="M60 38 C50 32 36 32 26 36 V86 C36 82 50 82 60 88 C70 82 84 82 94 86 V36 C84 32 70 32 60 38 Z" />
      <path d="M60 38 V88" />
      {/* page lines */}
      <g opacity="0.55">
        <path d="M34 50 h16 M34 60 h14 M70 50 h16 M70 60 h14" />
      </g>
      {/* accent spark */}
      <path
        d="M92 26 l2.4 5.6 5.6 2.4 -5.6 2.4 -2.4 5.6 -2.4 -5.6 -5.6 -2.4 5.6 -2.4 z"
        fill="var(--accent-2)"
        stroke="none"
      />
    </svg>
  )
}

export function EmptyQAArt({ size = 120, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {/* chat bubble */}
      <path d="M28 34 H80 A8 8 0 0 1 88 42 V70 A8 8 0 0 1 80 78 H50 L36 90 V78 H28 A8 8 0 0 1 20 70 V42 A8 8 0 0 1 28 34 Z" />
      {/* dots */}
      <g fill="currentColor" stroke="none">
        <circle cx="40" cy="56" r="2.6" />
        <circle cx="54" cy="56" r="2.6" />
        <circle cx="68" cy="56" r="2.6" />
      </g>
      {/* accent spark */}
      <path
        d="M94 30 l2.4 5.6 5.6 2.4 -5.6 2.4 -2.4 5.6 -2.4 -5.6 -5.6 -2.4 5.6 -2.4 z"
        fill="var(--accent-2)"
        stroke="none"
      />
    </svg>
  )
}
