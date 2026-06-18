# FDocs — Design Log

> Cập nhật: 2026-06-17 (Designer Worker pass 3 — KG Enhanced Interactivity spec)

---

## Confirmed Decisions

| # | Quyết định | Giá trị |
|---|---|---|
| 1 | UI Library | Tailwind CSS + shadcn/ui |
| 2 | Font (UI chrome) | Inter |
| 3 | Font (document content) | Merriweather |
| 4 | Theme system | CSS variables + `data-theme` attribute |
| 5 | Theme storage | localStorage |
| 6 | Navigation model | Fixed sidebar (240px) + collapsible to icon-only (56px) |
| 7 | Document layout | Split view: Text panel (45%) + Tools panel (55%) on ≥1280px; tab-based on 1024–1279px |
| 8 | Mode switching | Read / Understand = two tabs in same DocumentPage (NOT separate routes) |
| 9 | Focus mode | Collapse sidebar + text panel → centered 680px reading area (shortcut: `F`) |
| 10 | Mobile model | Single-column, bottom tab bar, Knowledge Graph disabled |
| 11 | KG Tooltip position | DOM-based (absolute trong canvas wrapper), không dùng Cytoscape label |
| 12 | KG Click deselect | Click lần 2 vào cùng node để deselect (không dùng Escape — conflict với Focus mode) |
| 13 | KG Legend position | bottom-right của canvas container (offset: 12px) |
| 14 | KG Table fallback tabs | 2 tabs riêng (Nodes / Edges) — không phải 1 table dài |
| 15 | KG Edge opacity mặc định | 0.7 để giảm visual noise; highlighted edges dùng opacity 1 |

---

## Theme Palette

### neutral (default)
```
--bg-base:      #F8FAFC   (slate-50)
--bg-surface:   #FFFFFF
--bg-muted:     #F1F5F9   (slate-100)
--border:       #E2E8F0   (slate-200)
--text-primary: #0F172A   (slate-900)
--text-muted:   #64748B   (slate-500)
--accent:       #4F46E5   (indigo-600)
--accent-hover: #4338CA   (indigo-700)
--accent-fg:    #FFFFFF
```

### cream (sepia / long reading)
```
--bg-base:      #FDFBF7
--bg-surface:   #FAF7F2
--bg-muted:     #F0EAE0
--border:       #E0D5C5
--text-primary: #3F3426
--text-muted:   #7C6E5C
--accent:       #B45309   (amber-700)
--accent-hover: #92400E   (amber-800)
--accent-fg:    #FFFFFF
```

### dark (scholar / night)
```
--bg-base:      #09090B   (zinc-950)
--bg-surface:   #18181B   (zinc-900)
--bg-muted:     #27272A   (zinc-800)
--border:       #3F3F46   (zinc-700)
--text-primary: #FAFAFA   (zinc-50)
--text-muted:   #A1A1AA   (zinc-400)
--accent:       #818CF8   (indigo-400)
--accent-hover: #6366F1   (indigo-500)
--accent-fg:    #FFFFFF
```

### Semantic Color Tokens (thêm mới — áp dụng cho cả 3 theme)

Thêm vào `index.css` dưới mỗi `[data-theme]` block:

```css
/* neutral & cream themes */
--success:      #10B981;
--success-bg:   #ECFDF5;
--warning:      #F59E0B;
--warning-bg:   #FFFBEB;
--error:        #EF4444;
--error-bg:     #FEF2F2;
--info:         #3B82F6;
--info-bg:      #EFF6FF;

/* dark theme — override above */
--success:      #34D399;
--success-bg:   rgba(16, 185, 129, 0.12);
--warning:      #FBBF24;
--warning-bg:   rgba(245, 158, 11, 0.12);
--error:        #F87171;
--error-bg:     rgba(239, 68, 68, 0.12);
--info:         #60A5FA;
--info-bg:      rgba(59, 130, 246, 0.12);
```

WCAG AA check:
- neutral: text-primary (#0F172A) on bg-base (#F8FAFC) → 16:1 ✅
- neutral: text-muted (#64748B) on bg-base (#F8FAFC) → 5.9:1 ✅
- cream: text-primary (#3F3426) on bg-base (#FDFBF7) → 13:1 ✅
- dark: text-primary (#FAFAFA) on bg-base (#09090B) → 19:1 ✅

### Theme Switch Transition

Thêm vào `:root` trong `index.css`:
```css
*, *::before, *::after {
  transition-property: background-color, border-color, color;
  transition-duration: 250ms;
  transition-timing-function: ease-in-out;
}
```
Áp dụng với `[data-theme]` để toàn bộ theme switch smooth — không cần JS.

---

## Layout Spec

### Desktop ≥1280px — DocumentPage Split View

```
┌──────────────────────────────────────────────────────────────────────┐
│ SIDEBAR 240px (fixed)      │  MAIN AREA (flex-1)                     │
│                            │                                         │
│ ┌────────────────────────┐ │ ┌─────────────────────────────────────┐ │
│ │ FDocs                  │ │ │ Doc title          [F] [⌘K] [Theme] │ │
│ │                        │ │ ├──────────────────┬──────────────────┤ │
│ │ ▸ Library              │ │ │ [Read] [Understand│]                 │ │
│ │ ▸ Upload               │ │ ├──────────────────┴──────────────────┤ │
│ │                        │ │ │  TEXT PANEL 45%  │  TOOLS PANEL 55% │ │
│ │ ─────────────────────  │ │ │  ──────────────  │  ──────────────  │ │
│ │ ⚠ Gemini Key           │ │ │  Merriweather    │  [Tab content]   │ │
│ │                        │ │ │  16px / lh 1.8   │                  │ │
│ │ [☀] [📄] [🌙]          │ │ │  max-w: 600px    │                  │ │
│ │ Logout                 │ │ │  px-8            │                  │ │
│ └────────────────────────┘ │ └──────────────────┴──────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Desktop 1024–1279px — Compact

- Sidebar: icon-only 56px (tooltip on hover for labels)
- Text panel: hidden by default; toggle button "[≡ Văn bản]" in header
- Tools panel: full width (flex-1)

### Mobile <768px

- Sidebar: removed; replaced by bottom tab bar (3 icons: Library / Upload / Account)
- DocumentPage: single column, tools panel stacked vertically
- Text panel: hidden, accessible via "Xem văn bản" button → full-screen overlay
- Knowledge Graph: show disabled card "Mở trên máy tính để tương tác với đồ thị"
- Read mode tabs: horizontal scrollable tab bar (overflow-x: auto)

---

## Typography Spec (Reading Area)

Applied to `.prose-reading` class (Merriweather content):

```css
.prose-reading {
  font-family: 'Merriweather', Georgia, serif;
  font-size: 16px;           /* 18px on ≥1440px */
  line-height: 1.85;
  max-width: 640px;
  letter-spacing: 0.01em;
}

.prose-reading p { margin-bottom: 1.25rem; }
.prose-reading h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem; }
.prose-reading h2 { font-size: 1.25rem; font-weight: 600; margin-bottom: 0.75rem; }
```

UI chrome (Inter) hierarchy:
- Page title: 18px / semibold
- Section header: 14px / semibold / uppercase tracking-wide
- Body: 14px / regular
- Caption/muted: 12px / regular
- Badge/label: 11px / medium

---

## Animation Spec

### Guiding Principles
1. **Purposeful** — mọi animation thông báo state change, không chỉ decoration
2. **Fast** — micro-interactions ≤ 200ms; AI loading ≤ 300ms initial appear
3. **Physics-based** — ease-in-out hoặc spring curves
4. **Respectful** — không animation khi `prefers-reduced-motion: reduce`

Thêm wrapper vào `index.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```

### Animation Table

| Element | Trigger | Duration | Easing | Spec |
|---|---|---|---|---|
| Page mount | Route change | 200ms | ease-out | `opacity: 0→1` + `translateY: 8px→0` |
| Sidebar collapse | Click toggle | 250ms | ease-in-out | `width: 240px→56px`, icon label opacity 1→0 |
| Text panel toggle | Click toggle | 200ms | ease-in-out | `width: 45%→0`, `opacity: 1→0` simultaneously |
| Mode tab switch | Click Read/Understand | 150ms | ease-in-out | Crossfade content `opacity: 0→1` |
| Modal open | Trigger | 200ms | cubic-bezier(0.34,1.56,0.64,1) | `scale: 0.96→1` + `opacity: 0→1` |
| Card hover | mouseenter | 150ms | ease-out | `translateY: 0→-2px` + `box-shadow` increase |
| Button press | mousedown | 80ms | ease-in | `scale: 1→0.97` |
| Button release | mouseup | 100ms | ease-out | `scale: 0.97→1` |
| Shimmer skeleton | Loading | 1500ms ∞ | linear | Background position sweep (see below) |
| Score bar fill | Data loaded | 700ms | cubic-bezier(0,0,0.2,1) | `width: 0→{value}%` left-to-right |
| Knowledge Graph | Generate | 1500ms | spring | COSE layout animate (already implemented) |
| Node appear (KG) | Layout starts | stagger 40ms | ease-out | COSE handles automatically |
| Q&A message in | New message | 200ms | ease-out | `translateY: 8px→0` + `opacity: 0→1` |
| Q&A cursor blink | Streaming | 900ms ∞ | linear | `opacity: 1→0→1` (already implemented) |
| Keyword tag appear | Result loaded | stagger 40ms/tag | cubic-bezier(0.34,1.56,0.64,1) | `scale: 0→1` + `opacity: 0→1` |
| Upload zone hover | dragenter | 150ms | ease-out | border-color → accent + `scale: 1→1.015` |
| Upload progress | Uploading | real-time | linear | Bar fill with trailing shimmer |
| Toast in | Event | 300ms | cubic-bezier(0.34,1.56,0.64,1) | Slide up from bottom-right + fade |
| Toast out | After 4s | 200ms | ease-in | `opacity: 1→0` + `translateY: 0→8px` |
| Theme switch | Click theme | 250ms | ease-in-out | CSS variable transition (see Theme section) |
| Focus mode enter | Click F | 300ms | ease-in-out | Sidebar width + text panel width → 0 |
| Focus mode exit | Esc | 250ms | ease-out | Reverse of enter |

### Shimmer Skeleton Spec

Thay thế `animate-pulse` bằng shimmer custom (hiện đại hơn):

```css
@keyframes shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-muted) 25%,
    var(--bg-surface) 50%,
    var(--bg-muted) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 4px;
}
```

Dùng cho: Summary panel, Keywords panel, bất kỳ nơi nào đang loading.

### Focus Mode

**Trigger:** Button `[⬚ Focus]` trong DocumentPage header, hoặc phím `F`  
**Exit:** `Esc` hoặc click `[✕ Exit Focus]`

Sequence:
1. Sidebar width → 0 (`250ms ease-in-out`)
2. Text panel expands to `max-w: 680px` centered in full viewport
3. Header minimizes: chỉ còn mode tabs + Exit button (`200ms`)
4. Tools panel: ẩn thành floating trigger button `[→ Analysis]` bottom-right
5. Background: `rgba(0,0,0,0.3)` overlay phía sau floating tools

---

## Component State Spec

### Button

| State | Visual |
|---|---|
| default | `bg-[--accent]`, white text, no border |
| hover | `bg-[--accent-hover]`, `translateY(-1px)`, `box-shadow: 0 4px 12px rgba(accent, 0.25)` |
| active | `scale(0.97)`, `translateY(0)`, shadow removed |
| disabled | `opacity: 0.4`, `cursor: not-allowed`, no hover effects |
| loading | Spinner replaces content, disabled state applied |
| ghost hover | `bg-[--bg-muted]`, no translateY |
| outline hover | `bg-[--bg-muted]`, `border-color: [--accent]` |

### Input

| State | Visual |
|---|---|
| default | `border: 1px solid [--border]`, `bg: [--bg-surface]` |
| focus | `ring: 2px solid [--accent]`, `border-color: [--accent]` |
| error | `ring: 2px solid [--error]`, `border-color: [--error]` |
| disabled | `opacity: 0.5`, `cursor: not-allowed`, `bg: [--bg-muted]` |

### Card

| State | Visual |
|---|---|
| default | `border: 1px solid [--border]`, `bg: [--bg-surface]`, `shadow: 0 1px 3px rgba(0,0,0,0.05)` |
| hover (clickable) | `shadow: 0 4px 12px rgba(0,0,0,0.08)`, `translateY(-2px)`, `transition: 150ms ease-out` |
| selected | `border-color: [--accent]`, `ring: 2px [--accent] inset` |

---

## Differentiation Features

### ✅ IMPLEMENTED

#### #1 — Animated Knowledge Graph Construction
- COSE layout với `animate: true, animationDuration: 1500`
- Node colors sync với active theme
- Status: Done

#### #3 — Command Palette (Cmd/Ctrl + K)
- cmdk library, integrated trong AppLayout
- Status: Done

#### #5 — SSE Streaming Q&A
- EventSource + typewriter cursor
- Status: Frontend done; backend refactor pending (StreamingResponse)

---

### ✅ DESIGN COMPLETE — Sẵn sàng để Frontend implement

#### #2 — Library as Similarity Map

**ADR**: Hybrid view toggle — Grid (default) | Map view (toggle button)

**Map view spec:**
- Library: thêm toggle button `[⊞ Grid] [◉ Map]` ở top-right của LibraryPage
- Map view: Cytoscape.js instance thay thế grid
  - Node: circle, diameter 64px, truncated title (max 2 lines, 11px)
  - Node color: accent color, opacity biến đổi theo word_count (nhiều từ → đậm hơn)
  - Edge: hiện khi `similarity_score > 0.65` (ngưỡng quyết định — đủ signal, không noise)
  - Edge thickness: linear map `0.65→1.0` thành `1px→4px`
  - Layout: Cytoscape `cose` (không cần install thêm plugin)
  - **Hover node**: ring highlight `3px [--accent]` + tooltip tên document + highlight connected edges (opacity 1) + dim unconnected edges (opacity 0.2)
  - **Click node**: `navigate('/document/:id')`
  - **Empty state** (<2 docs): "Upload ít nhất 2 tài liệu để xem bản đồ tương đồng"
  - **No edges** (tất cả similarity < 0.65): "Các tài liệu trong library chưa đủ liên quan để vẽ liên kết"

**Backend endpoint cần thêm** (giao Backend Worker):
```
GET /api/library/similarity-map
Authorization: Bearer <token>
X-Gemini-Key: <key>

Response 200:
{
  "nodes": [{ "id": "uuid", "title": "string", "word_count": 12500, "file_type": "pdf" }],
  "edges": [{ "source": "uuid", "target": "uuid", "similarity": 0.82 }]
}
```

Algorithm: all-pairs cosine similarity giữa document centroid embeddings (đã có `get_doc_embedding_centroid` trong ChunkRepository). Filter edges < 0.65.

---

#### #4 — Reading Heatmap Overlay

**ADR**: Inline text highlight overlay, toggled on/off

**Spec:**
- Toggle button `[🔥 Heatmap]` trong DocumentPage header, chỉ hiện khi có ≥1 Q&A history item với sources
- Khi active: extracted text được render với `<mark>` tags tại vị trí chunk tương ứng
- Color scale theo số lần chunk được cite trong qa_history:
  - 1 cite: `background: rgba(245, 158, 11, 0.15)` (amber faint)
  - 2–3 cites: `background: rgba(245, 158, 11, 0.35)` (amber medium)
  - 4+ cites: `background: rgba(239, 68, 68, 0.40)` (red hot)
- Hover `<mark>`: tooltip hiện "Được trích dẫn {n} lần" + danh sách câu hỏi có cite chunk này (truncated 60 chars)

**Implementation approach (Frontend):**
1. `qa_history` trả về mỗi item có `sources: [{ chunk_id, chunk_index, content_preview }]`
2. Count `chunk_index` citations: `Map<chunk_index, count>`
3. Split `extracted_text` thành chunks theo `chunk_index` (dùng cùng logic chia ~1800 chars / chunk để khớp với backend splitter)
4. Render từng chunk: nếu `chunk_index` có trong map → wrap trong `<mark data-count={n}>`, không thì `<span>`
5. Tooltip dùng `title` attribute hoặc custom Tooltip component

**Backend cần thêm vào `qa_history` response**: `sources` array với `chunk_index` field. Hiện tại sources có `chunk_id` — cần JOIN với `chunks` table để lấy `chunk_index`.

---

## Micro-interaction Catalogue

### Upload Zone (UploadPage)
- idle: dashed border `[--border]`, `bg-[--bg-muted]`
- `dragenter` (valid): accent border `[--accent]` + `bg: rgba(accent, 0.05)` + icon bounce (translateY -4px → 0, spring 300ms) + text "Thả file để upload"
- `dragenter` (invalid MIME): red border `[--error]` + `bg: rgba(error, 0.05)` + text "Chỉ hỗ trợ PDF và DOCX"
- `dragleave`: revert to idle (`150ms ease-out`)
- processing: progress bar full-width bottom of zone, gradient fill with trailing shimmer

### Knowledge Graph
- Node hover: `ring: 3px [--accent]` + label background darken + `cursor: pointer`
- Node click: zoom center on node (Cytoscape `animate: true`) + connected edges highlight (opacity 1) + others dim (opacity 0.2) — "ego network" view
- Edge hover: width `1.5px → 3px` + label font-size `9px → 11px` + label background `[--bg-surface]`
- Pan: `cursor: grab` → `cursor: grabbing`
- "Fit" button: `cy.fit(30)` with animation (already implemented)
- Double-click node: `cy.fit(connectedElements, 40)` — zoom to ego network

### Q&A Chat
- Input focus: border → accent, ring appear (`150ms`)
- Send button: hover → `scale(1.05)` pulse
- New message: `translateY(8px) opacity(0) → translateY(0) opacity(1)` (`200ms ease-out`)
- Sources expand: accordion with `height: 0 → auto` + `opacity: 0→1` (`200ms`)
- Streaming "thinking" state: show `●●●` animated indicator ở header ("Đang tìm kiếm...")

### Keyword Tags
- Load sequence: stagger 40ms per tag, `scale(0) → scale(1)` + `opacity(0→1)` với spring easing
- Hover: `scale(1.05)` + background darken slightly
- Click (future): filter/search by keyword

---

## Accessibility Spec

- Tất cả icon-only buttons có `aria-label`
- `:focus-visible` ring trên mọi interactive element (dùng Tailwind `focus-visible:ring-2`)
- Màu không phải indicator duy nhất — luôn pair với icon hoặc text
- Tab order: Sidebar nav → Header actions → Main content
- KG graph: thêm button `[Xem dạng bảng]` mở modal với table `nodes` và `edges` cho screen reader
- Keyboard shortcuts: document trong Command Palette (`?` shortcut để xem list)
- `role="article"` cho extracted text reading area
- Skip link: `<a href="#main-content" className="sr-only focus:not-sr-only">Skip to content</a>`

---

## Open Design Questions — RESOLVED

| # | Câu hỏi | Quyết định |
|---|---|---|
| 1 | Navigation model | Fixed sidebar 240px, collapsible to 56px icon-only (shortcut: `\`) |
| 2 | Read vs Understand mode | Hai tabs trong cùng DocumentPage — KHÔNG phải route riêng |
| 3 | Extracted text panel | Split view (45/55 default) trên ≥1280px; toggle button trên 1024–1279px |
| 4 | Mobile (375px) | Single column; bottom tab bar; KG disabled; Summary + Keywords + Q&A prioritized |

---

## Handoff Checklist cho Frontend Worker

### Implement ngay (P0)

- [ ] **Thêm semantic color tokens** vào `index.css` (success/warning/error/info, tất cả 3 theme)
- [ ] **Theme switch transition** — thêm CSS transition vào `*, *::before, *::after`
- [ ] **Shimmer skeleton** — thêm `@keyframes shimmer` + `.skeleton` class, replace `animate-pulse` trong SummaryPanel + KeywordsPanel
- [ ] **Keyword tags stagger animation** — trong KeywordsPanel, add `style={{ animationDelay: \`${i*40}ms\` }}` + CSS fade+scale
- [ ] **Page mount animation** — trong AppLayout hoặc từng page, wrap content với `animate-[fadeSlideUp]`
- [ ] **Card hover animation** — update Card.jsx với `hover:-translate-y-0.5 hover:shadow-md transition-all duration-150`
- [ ] **Sidebar collapse** — thêm toggle button `[\]` trong sidebar header; khi collapsed show 56px icon-only; sidebar state persist localStorage
- [ ] **Text panel toggle** — thêm button `[≡]` trong DocumentPage header; text panel width transition; persist preference
- [ ] **Focus mode** — button `[⬚]` trong header, phím `F` shortcut; sidebar + text panel collapse; Tools floating button
- [ ] **`prefers-reduced-motion`** wrapper trong `index.css`
- [ ] **Semantic color tokens** — dùng `var(--success)` / `var(--error)` trong error states, badges, upload feedback

### Implement sau — KG Enhanced Interactivity (P1 — Design COMPLETE)

> Spec đầy đủ tại: `docs/KG_DESIGN_SPEC.md`

- [ ] **KG Edge label improvement** — font-size 10px + text-background-color pill + opacity 0.7
- [ ] **KG Legend** — DOM element absolute bottom-right, 3 rows (concept/entity/process), `hidden sm:flex`
- [ ] **KG Hover tooltip** — DOM-based, 120ms delay, flip logic ở rìa canvas, fade-in animation
- [ ] **KG Click highlight** — Cytoscape class system: `selected` / `highlighted` / `dimmed`; double-click zoom ego network; click empty space reset
- [ ] **KG Accessibility Table** — toggle button `[Table view]` trong header; component `KGTable.jsx`; 2 tabs (Nodes/Edges); sticky header; proper ARIA

### Implement sau (P1 — Design Pending đã resolve)

- [ ] **Library Map view toggle** — thêm `[⊞] [◉]` toggle, Cytoscape map view với node/edge spec trên
  - Cần backend endpoint `GET /api/library/similarity-map` trước
- [ ] **Reading Heatmap** — toggle button `[🔥]` trong DocumentPage header, chunk split + mark render
  - Cần backend update `qa_history` response để include `chunk_index` trong sources

### Đã done (không cần làm lại)
- [x] 3-theme CSS variables
- [x] ThemeProvider + ThemeSwitcher
- [x] COSE animated Knowledge Graph
- [x] Command Palette (⌘K)
- [x] Q&A typewriter cursor
- [x] SummaryPanel skeleton (upgrade to shimmer)
- [x] Score bar animation (RelevancePanel)

---

## Designer Worker — Pass 4 (2026-06-18): Decorative & Vibrancy Layer

> Mục tiêu: làm web sinh động hơn (pattern/màu phụ/animation/illustration/typography) **mà KHÔNG phá** hệ thống đã confirm. Nguyên tắc xuyên suốt: **vùng đọc/Q&A giữ tĩnh & sạch; chỉ trang trí ở vùng marketing/auth/upload/empty-state/sidebar.** Đây là SPEC để Frontend implement sau khi PM duyệt — chưa code.

### Nguyên tắc phân vùng trang trí
| Vùng | Mức trang trí | Lý do |
|---|---|---|
| Auth / Landing / Upload / Empty-state | **Cao** — pattern, gradient, illustration, display font | Chưa đọc nội dung → cần "wow", tạo nhận diện |
| Sidebar / Header chrome | **Vừa** — accent phụ, micro-interaction | Khung điều hướng, không phải nội dung |
| Reading area / Q&A / KG canvas | **Tối thiểu** — chỉ giữ nội dung | Đọc lâu, công thức → mọi họa tiết = nhiễu |

### A. Palette mở rộng (thêm token, KHÔNG đổi `--accent` brand)
Giữ `--accent` indigo (#4F46E5 neutral / #818CF8 dark / #B45309 cream) làm brand cho mọi action chính. **Thêm**:

| Token | neutral | dark | cream | Dùng cho |
|---|---|---|---|---|
| `--accent-2` (secondary) | `#06B6D4` (cyan-500) | `#22D3EE` | `#0E7490` | Illustration, biểu đồ, highlight phụ — KHÔNG dùng cho nút primary |
| `--accent-2-soft` | `#CFFAFE` | `rgba(34,211,238,.14)` | `#CFFAFE` | Nền chip/badge phụ |
| `--decor-grid` | `rgba(79,70,229,.05)` | `rgba(129,140,248,.07)` | `rgba(180,83,9,.05)` | Màu pattern dot/grid (rất mờ) |
| `--gradient-hero` | `linear-gradient(135deg,#4F46E5 0%,#06B6D4 100%)` | `linear-gradient(135deg,#818CF8,#22D3EE)` | `linear-gradient(135deg,#B45309,#D97706)` | Nền hero auth/landing |

Lý do cyan làm phụ: bổ trợ (analogous-cool) với indigo, gợi cảm giác "tri thức/khoa học", tương phản tốt mà không chọi brand. Contrast: dùng `--accent-2` chủ yếu cho mảng lớn/illustration, text trên nền cần kiểm WCAG AA riêng.

### B. Pattern / họa tiết (chủ đề học thuật)
- **Dot-grid** (radial-gradient, không ảnh): chấm 1px, khoảng cách ~22px, màu `--decor-grid`, opacity ≤ 0.06. Dùng: nền trang Auth, Upload, Empty-state. **Reading area: không.**
- **Academic glyph motif**: SVG mờ các ký hiệu toán (∑ ∫ √ ‖x‖ π) + node/edge kiểu knowledge-graph, opacity 0.04–0.05, đặt góc hero/empty-state làm "texture" gợi đúng chủ đề tài liệu học thuật + KG. Tĩnh, không animate trong vùng có chữ.
- **Sidebar footer**: 1 dải dot-grid mờ phía dưới logo cho đỡ trống — mức vừa.
- Quy tắc: pattern luôn dưới `z-index` nội dung, `pointer-events:none`, opacity đủ thấp để text trên nó vẫn đạt contrast AA.

### C. Typography (điểm nhấn user quan tâm)
Giữ confirmed: **Inter** (UI) + **Merriweather** (reading). **Thêm 1 display font cho heading marketing/hero/empty-state** (KHÔNG đổi body):
- Đề xuất **"Fraunces"** (serif display, có optical sizing, cá tính học thuật-cổ điển nhưng hiện đại) HOẶC **"Spectral"** — chỉ dùng ở H1/H2 landing/auth/empty-state, size ≥ 28px.
- Token: `--font-display`. Scale gợi ý: hero H1 40–56px / weight 600 / line-height 1.1 / letter-spacing -0.01em.
- **Cảnh báo tiếng Việt (cần verify)**: kiểm tra dấu tiếng Việt (ặ, ỡ, ệ…) render đúng ở Merriweather & display font. Nếu Merriweather xếp dấu chưa đẹp với nội dung VN dài → cân nhắc **"Lora"** hoặc **"Be Vietnam Pro"** (VN-first) cho `.prose-reading`. Đây là điểm cần test thực tế trước khi chốt.
- **Nguồn font (perf + privacy)**: hiện đang `@import` Google Fonts trong index.css — chặn render + lộ IP người dùng cho Google (mâu thuẫn định vị "privacy-first/BYOK"). **Khuyến nghị self-host** (woff2 trong `/public/fonts` + `@font-face` + `font-display: swap`), hoặc tối thiểu thêm `<link rel="preconnect">`. Chỉ nạp weight thực dùng.

### D. Transition / Animation (bổ sung, theo nguyên tắc đã có)
Tuân thủ `## Animation Spec` cũ + `prefers-reduced-motion` (đã có trong index.css). Thêm:
| Hiệu ứng | Trigger | Spec | Vùng |
|---|---|---|---|
| Aurora/gradient mesh động | mount | gradient `--gradient-hero` dịch chuyển rất chậm (20–30s, ease-in-out, infinite) | Hero auth/landing |
| Float nhẹ illustration | mount | translateY ±6px, 6s ease-in-out alt | Empty-state |
| Dot-grid parallax (tuỳ chọn) | scroll | dịch ≤8px theo scroll | Landing |
| Stagger card vào | list mount | dùng `animate-tag-in` đã có, delay 40ms/item | Library/Upload list |
Tất cả hiệu ứng nền/lặp **phải tắt** khi `prefers-reduced-motion: reduce`. Vùng đọc/Q&A: không thêm animation nền.

### E. Illustration / hình ảnh
- **Có nên**: CÓ, nhưng chỉ **line-art SVG đơn sắc** (dùng `--accent`/`--accent-2`), nhẹ, không raster nặng. Chủ đề: sách mở, trang giấy + công thức, mạng node-edge (tri thức). Dùng ở **empty-state** (chưa có tài liệu/câu hỏi), **onboarding**, **404**.
- **KHÔNG**: ảnh stock/raster lớn ở vùng đọc; không hero image nặng làm chậm LCP.
- Nguồn: tự vẽ SVG hoặc bộ open (unDraw — chỉnh màu theo accent). Inline SVG để đổi màu theo theme.

### F. Lỗi nhất quán phát hiện (cần sửa nhỏ)
- `frontend/index.html` đặt `theme-color #6c5ce7` **không khớp** accent thật `#4F46E5`. → Sửa về `#4F46E5` (hoặc theo theme mặc định).

### Khuyến nghị ưu tiên (impact cao / chi phí thấp trước)
1. **P0 (rẻ, làm trước)**: sửa theme-color (#4F46E5); thêm dot-grid pattern cho Auth + Empty-state; self-host/preconnect font; thêm `--accent-2` + `--gradient-hero` tokens.
2. **P1**: display font (`--font-display`) cho heading auth/landing/empty-state + refine type scale; line-art SVG empty-states.
3. **P2**: aurora gradient động ở hero auth/landing; pattern sidebar footer; verify & (nếu cần) đổi reading font cho tiếng Việt.

> **Quyết định cần PM/user chốt trước khi Frontend implement**: (1) chọn display font (Fraunces vs Spectral); (2) reading font tiếng Việt giữ Merriweather hay đổi Lora/Be Vietnam Pro; (3) self-host font hay giữ Google Fonts. Ba câu này ảnh hưởng asset + privacy.

### Pass 4 — Quyết định đã chốt (user, 2026-06-18)
| Vấn đề | Chốt | Ghi chú |
|---|---|---|
| Display font (heading marketing/empty-state) | **Fraunces** | `--font-display`, chỉ H1/H2 vùng marketing/auth/empty-state; body vẫn Inter |
| Reading font tiếng Việt | **Giữ Merriweather** | ⚠️ Frontend/Tester verify dấu tiếng Việt (ặ, ỡ, ệ) render đẹp khi đọc dài; nếu lỗi → escalate lại Designer |
| Font hosting | **Giữ Google Fonts** (`@import`) | Chấp nhận đánh đổi privacy/perf ở giai đoạn này; thêm Fraunces vào dòng `@import` hiện có. Có thể self-host sau nếu cần |

### Pass 4 — Cập nhật `--gradient-hero` (2026-06-18): bỏ cyan, về mono-brand tím

**Vấn đề** (user feedback, verify bằng harness headless): aurora indigo→cyan ở opacity rõ (.35) khiến nền auth ngả **teal/sky**, lệch nhận diện indigo của FDocs (dark còn xanh-lục rõ hơn). Đầu cyan `--accent-2` không bổ trợ tốt khi làm mảng nền lớn.

**Quyết định: Phương án A — indigo → violet (monochrome brand).** Giữ toàn gradient trong họ tím → coherent, sang, không "đổi màu". So sánh A/C/hiện-tại trên light+dark: A giữ bản sắc tốt nhất mà vẫn có chuyển màu sống động (hơn C blue-violet hơi đơn điệu).

`--gradient-hero` mới:
| Theme | Cũ (có cyan) | **Mới (mono tím)** |
|---|---|---|
| neutral | `#4F46E5 → #06B6D4` | **`#4F46E5 → #A78BFA`** |
| dark | `#818CF8 → #22D3EE` | **`#6366F1 → #A78BFA`** |
| cream | `#B45309 → #D97706` | **giữ nguyên** (đã là mono ấm, không dính cyan) |

**Opacity aurora**: hạ `.35 → .30` (gradient mono-brand đỡ gắt hơn cyan nên .30 đủ "sống" mà không lấn card).

**`--accent-2` (cyan #06B6D4) GIỮ NGUYÊN** — vẫn dùng cho illustration/spark/biểu đồ. Quyết định này CHỈ đổi `--gradient-hero`.

Handoff Frontend: đổi 2 dòng `--gradient-hero` (neutral, dark) trong index.css + hạ `.auth-aurora` opacity `.35 → .30`. Cream giữ nguyên. Verify card+text vẫn nổi.

### Pass 4 — Quyết định cuối: bỏ aurora hoàn toàn (2026-06-18)

**Quyết định (user)**: Dù đã đổi sang mono-violet (phương án A) trông tốt hơn cyan, user vẫn quyết định **không dùng aurora gradient** — lý do: gradient nền lớn ở auth không phù hợp phong cách tổng thể sản phẩm (mục tiêu reading app học thuật, tối giản). Gradient hero làm auth trông "landing page commercial" hơn "scholarly tool".

**Thực hiện**:
- Xóa `<div className="auth-aurora" />` khỏi `AuthLayout.jsx`
- Xóa `.auth-aurora {}` block và `@keyframes auroraShift` khỏi `index.css`
- **Giữ** token `--gradient-hero` (design token, có thể tái dùng cho button/banner nhỏ sau này)
- **Giữ** tất cả: dot-grid, cursor spotlight, Fraunces, float animation, illustration, sidebar footer dot-grid

**Trạng thái auth page sau P2**: nền sạch (`--bg-base`) + dot-grid tĩnh + spotlight theo chuột — đủ character mà không lấn nội dung card.
