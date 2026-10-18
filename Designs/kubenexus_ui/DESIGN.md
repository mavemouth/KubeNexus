---
name: KubeNexus UI
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#bdc8d1'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#87929a'
  outline-variant: '#3e484f'
  surface-tint: '#7bd0ff'
  primary: '#8ed5ff'
  on-primary: '#00354a'
  primary-container: '#38bdf8'
  on-primary-container: '#004965'
  inverse-primary: '#00668a'
  secondary: '#a4c9ff'
  on-secondary: '#00315d'
  secondary-container: '#0267b8'
  on-secondary-container: '#d6e5ff'
  tertiary: '#56e5a9'
  on-tertiary: '#003824'
  tertiary-container: '#30c88f'
  on-tertiary-container: '#004e34'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c4e7ff'
  primary-fixed-dim: '#7bd0ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c69'
  secondary-fixed: '#d4e3ff'
  secondary-fixed-dim: '#a4c9ff'
  on-secondary-fixed: '#001c39'
  on-secondary-fixed-variant: '#004883'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  headline-sm:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  code-snippet:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system is engineered for developer tooling, cloud infrastructure observability, and algorithmic cost attribution. The visual narrative balances technical precision with high-density utility, tailored for engineering teams and infrastructure operators managing clusters at scale.

The aesthetic philosophy centers on **Technical Glassmorphism & High-Precision Dark Mode**:
- **Controlled Translucency:** Interfaces rely on layered deep navy glass surfaces, muted slate structural lines, and restrained backdrop blurs rather than heavy opaque layers.
- **Signal-to-Noise Focus:** Bright neon tints are strictly reserved for operational state (cluster health, memory thrashing, CPU limits, projected cost delta).
- **Engineered Calm:** Dense metrics, node allocation charts, and workload trees sit comfortably against low-luminance navy backdrops to reduce visual fatigue during prolonged incident triage.

## Colors

The system employs a cold, high-legibility spectrum constructed specifically for high-contrast dark environments.

### Surface System
- **Canvas Base:** `#090d16` (Primary dark viewport canvas)
- **Layer 0 (Underlay):** `#0d1527` (Sidebars, command bars, canvas grouping)
- **Layer 1 (Card / Container):** `rgba(19, 30, 54, 0.72)` with a 1px border of `rgba(51, 65, 85, 0.35)`
- **Layer 2 (Elevated Popovers & Modals):** `rgba(24, 38, 68, 0.90)` with border `rgba(96, 165, 250, 0.20)`

### Accent & Semantic Tokens
- **Primary Brand (Sky Blue):** `#38bdf8` — Active states, metric focal lines, primary triggers, and active cluster selection.
- **Secondary (Slate Blue):** `#60a5fa` — Interactive secondary tools, links, and secondary metric series.
- **Telemetry Health / Savings (Emerald):** `#10b981` (Base), `#34d399` (Accent/Badge) — Healthy pods, node savings, cost recovery markers.
- **Telemetry Warning (Amber):** `#f59e0b` — Node pressure, disk near limit, approaching budget caps.
- **Telemetry Critical (Crimson):** `#ef4444` — Pod crash loops, OOMKilled events, resource starvation.
- **Typography & Structure:** Primary Text `#f8fafc`, Secondary Text `#94a3b8`, Tertiary/Muted `#64748b`.

## Typography

Typography prioritizes dense tabular scanability and micro-level clarity.

- **Primary Typeface (`Inter`):** Powers product titles, operational metric labels, and descriptive narrative. Configured with tabular figures (`tnum`) across all telemetry dashboards to prevent layout shifts during live polling.
- **Monospaced Utility (`JetBrains Mono`):** Applied to Kubernetes resource addresses (`namespace/pod-uid`), IP routing tables, resource allocations (`500m`, `2Gi`), and shell log outputs.
- **Optical Hierarchy:** Small labels (`11px` - `13px`) use wide tracking (`letter-spacing: 0.04em`) to maintain legibility against dark translucent backing.

## Layout & Spacing

The system runs on a 4px/8px incremental grid tailored for high-information density dashboards.

### Grid & Breakpoints
- **Desktop (≥ 1280px):** 12-column responsive fluid grid with 24px gutters and fixed 64px collapsed / 240px expanded navigation rail. Maximum viewport ceiling is uncapped for multi-monitor NOC displays.
- **Tablet (768px – 1279px):** 8-column layout with 16px gutters; sub-metrics reflow to vertical stack tabs.
- **Mobile (< 768px):** 4-column layout with 16px lateral padding; high-level cluster KPIs collapse to swipeable horizontal cards while workload tables transition to aggregated status lists.

### Spatial Discipline
Inner card padding adheres strictly to `space-md` (16px) for standard widgets and `space-lg` (24px) for high-impact analytical charts to preserve visual balance without wasting operational screen real estate.

## Elevation & Depth

Visual hierarchy does not use high-drop drop shadows; instead, it uses luminous borders, surface luminescence, and backdrop blur.

- **Base Level (Canvas):** Pure `#090d16`. Zero blur.
- **Level 1 (Monitoring Panels & Data Cards):** Background `rgba(19, 30, 54, 0.70)`, border `1px solid rgba(51, 65, 85, 0.40)`, backdrop filter `blur(12px)`.
- **Level 2 (Hover States & Dropdowns):** Background `rgba(26, 42, 74, 0.85)`, border `1px solid rgba(56, 189, 248, 0.35)`, backdrop filter `blur(16px)`, box shadow `0 8px 32px -4px rgba(0, 0, 0, 0.50), 0 0 12px 0 rgba(56, 189, 248, 0.08)`.
- **Level 3 (Diagnostic Drawers & Modals):** Background `rgba(13, 21, 39, 0.95)`, border `1px solid rgba(96, 165, 250, 0.30)`, backdrop filter `blur(24px)`, box shadow `0 24px 48px -12px rgba(0, 0, 0, 0.75)`.

## Shapes

The shape vocabulary maintains a contemporary, precision-engineered personality.

- **Structural Containers & Surface Cards:** Standardized to `12px` (`rounded-lg`), achieving an approachable yet modern profile that softens dense data presentation.
- **Interactive Controls (Inputs, Buttons):** Set to `8px` (`rounded-md`) to ensure tactile differentiation from parent cards.
- **Telemetry Badges & Health Pills:** Fully rounded (`9999px` / pill-shaped) to distinguish quick-scan status metrics from square structural cards.

## Components

### Buttons
- **Primary:** Solid `#38bdf8` with `#090d16` bold text, radius `8px`. Hover: `#60a5fa` with `0 0 16px rgba(56, 189, 248, 0.35)`.
- **Secondary / Glass:** Background `rgba(30, 41, 59, 0.60)`, border `1px solid rgba(100, 116, 139, 0.30)`, text `#f8fafc`. Hover: background `rgba(51, 65, 85, 0.80)`.
- **Ghost:** Transparent background, text `#94a3b8`. Hover: text `#f8fafc`, background `rgba(255, 255, 255, 0.05)`.

### Telemetry Badge Pills
Compact status markers featuring an internal glowing 6px status indicator circle:
- **Optimal (Savings/Healthy):** Background `rgba(16, 185, 129, 0.12)`, border `rgba(16, 185, 129, 0.25)`, text `#34d399`.
- **Warning (Pressure):** Background `rgba(245, 158, 11, 0.12)`, border `rgba(245, 158, 11, 0.25)`, text `#fbbf24`.
- **Critical (Degraded):** Background `rgba(239, 68, 68, 0.12)`, border `rgba(239, 68, 68, 0.25)`, text `#f87171`.

### Data Cards & Metric Tiles
Cards host a compact top header (uppercase `label-sm` muted text), a massive `headline-lg` numerical value, and a bottom micro-sparkline or percentage change indicator. Background remains translucent with a top subtle 1px accent highlight gradient.

### Input Fields & Search Bars
- Background `rgba(15, 23, 42, 0.70)`, border `1px solid rgba(51, 65, 85, 0.50)`, radius `8px`, text `#f8fafc`, placeholder `#64748b`.
- Focus state: border `#38bdf8`, box-shadow `0 0 0 2px rgba(56, 189, 248, 0.20)`.

### Checkboxes & Radios
- Size: 16px × 16px. Border `1px solid rgba(148, 163, 184, 0.40)`. Background `rgba(15, 23, 42, 0.80)`.
- Checked: Background `#38bdf8`, tick/bullet icon `#090d16`.

### Pod & Node Density Lists
Workload rows utilize alternating soft zebra hover treatments (`rgba(56, 189, 248, 0.04)`), compact `36px` row heights for maximal vertical metric density, and monospaced right-aligned numeric tables.