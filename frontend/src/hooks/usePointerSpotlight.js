import { useEffect, useRef } from 'react'

/**
 * Tracks the pointer over the returned ref'd element and writes its position
 * into CSS vars `--mx`/`--my` (px, relative to the element). A `.decor-spotlight`
 * mask reads these to reveal a brighter dot patch around the cursor.
 *
 * - rAF-throttled: at most one DOM write per frame, no React re-render.
 * - Disabled under `prefers-reduced-motion: reduce` (no listener attached).
 */
export function usePointerSpotlight() {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return

    let frame = 0
    let nextX = 0
    let nextY = 0

    const flush = () => {
      frame = 0
      el.style.setProperty('--mx', `${nextX}px`)
      el.style.setProperty('--my', `${nextY}px`)
    }

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      nextX = e.clientX - rect.left
      nextY = e.clientY - rect.top
      if (!frame) frame = requestAnimationFrame(flush)
    }

    el.addEventListener('mousemove', onMove)
    return () => {
      el.removeEventListener('mousemove', onMove)
      if (frame) cancelAnimationFrame(frame)
    }
  }, [])

  return ref
}
