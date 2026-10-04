# KageX — Design Reference Specification

This document captures the visual language, design system, layout principles, components, typography, animations, and UX patterns defined in `docs/DESIGN.md` and visualized in `docs/design.html` for KageX.

---

## 1. Visual Language & Aesthetic Identity

- **Design Tone**: "Operational Elegance" — brutalist data density meets classical typography and refined enterprise control tower aesthetic.
- **Core Philosophy**: High signal-to-noise ratio, crisp borders, subtle inset highlights, radial depth gradients, and safety/signal orange for active/critical states.
- **Background Foundation**: Tan / warm light gray background (`#f6f5f2`) combined with a fixed radial gradient (`radial-gradient(circle at 50% 14%, rgba(255,255,255,0.96), rgba(246,245,242,0.76) 48%, rgba(238,236,232,0.92) 100%)`).

---

## 2. Color System & Tokens

### Base & Surfaces
| Token | Hex / Value | Usage |
|---|---|---|
| **Background Tan** | `#f6f5f2` | Primary page canvas background |
| **Background Dark** | `#111111` / `#1b1c1b` | Primary dark surface, high-contrast hero/cards, primary buttons |
| **Surface White** | `#ffffff` | Elevated metric cards, badges, inner containers |
| **Surface Glass Light** | `rgba(255, 255, 255, 0.35)` to `0.88` | Translucent frosted cards with `backdrop-blur-sm` |
| **Border Light** | `rgba(0, 0, 0, 0.10)` / `rgba(0, 0, 0, 0.15)` | Standard card and section dividing borders |
| **Border Dark/Highlight** | `rgba(255, 255, 255, 0.12)` / `rgba(255, 255, 255, 0.45)` | Inset rim highlights on dark cards |

### Signal & Accent Colors
| Token | Hex / Value | Usage |
|---|---|---|
| **Signal / Primary Orange** | `#ff5a24` | Primary brand accent, active signals, pulse indicators, hero highlights |
| **Signal Orange Light** | `#ff6330` / `#ff8a5c` | Conic gradients, hover states, sparklines |
| **Text Main (Dark)** | `#000000` / `#090909` | H1/H2 headings, primary metrics, dark titles |
| **Text Secondary** | `#222222` / `#252525` / `#333333` | Body copy, secondary titles, card descriptions |
| **Text Muted** | `#6a6a6a` / `#7a7a7a` / `#8a8a8a` | Metadata, timestamps, table headers, subtitles |
| **Text Inverted** | `#ffffff` / `rgba(255, 255, 255, 0.90)` | Text on dark cards and primary buttons |

---

## 3. Typography Hierarchy

### Font Families
- **Display Serif**: `Playfair Display`, Georgia, serif (Weights: 400, 500, Medium, Italic)
  - *Application*: H1/H2 hero titles, section headlines, decorative numbers, emphasized keywords (often styled in italic orange).
- **Functional Sans**: `Inter`, ui-sans-serif, system-ui, sans-serif (Weights: 400, 500, 600)
  - *Application*: Navigation, KPI readouts, buttons, tables, metadata, status labels, controls.

### Type Scale & Letter Spacing
- **H1 Headline**: `text-5xl` to `text-7xl` (`font-medium leading-[0.96] tracking-tight`)
- **H2 Section Headline**: `text-5xl` to `text-7xl` (`font-medium leading-[0.95] tracking-tight`)
- **H3 Card Headline**: `text-3xl` to `text-4xl` (`font-medium` or `font-semibold tracking-tight`)
- **Category Labels / Signal Tags**: `text-sm` to `text-lg` (`font-normal uppercase tracking-wide` or `tracking-[0.22em]`)
- **Primary Metrics / Numeric KPI**: `text-4xl` to `text-6xl` (`font-normal tracking-tight leading-none`)
- **Body Text**: `text-base` to `text-xl` (`font-normal leading-snug text-[#252525]` or `#333333`)
- **Metadata / Subtext**: `text-xs` to `text-sm` (`font-normal text-[#7a7a7a]` / `#8a8a8a`)

---

## 4. Spacing, Layout & Grid Systems

- **Max Container Width**: `max-w-[112rem]` (1792px)
- **Responsive Padding**:
  - Mobile: `px-6 pt-12 pb-14`
  - Tablet: `sm:px-10`
  - Desktop: `lg:px-16 lg:py-24`
- **Grid Layouts**:
  - Hero Split: `grid lg:grid-cols-[0.77fr_1.23fr] gap-10 xl:gap-14`
  - 3-Column Feature Cards: `grid lg:grid-cols-3 gap-8`
  - 2-Column Split: `grid lg:grid-cols-[0.7fr_1fr] gap-7`
  - Step Flow Grid: `grid lg:grid-cols-[1fr_2.5rem_1fr_2.5rem_1fr] gap-7`
- **Corner Radii**:
  - Buttons / Controls: `rounded-md` (6px) to `rounded-lg` (8px)
  - Standard Cards: `rounded-xl` (12px) to `rounded-2xl` (16px)
  - Hero Container / Operational Mirrors: `rounded-[2.7rem]` (43px)
  - Pill Badges & Toggle Switches: `rounded-full` (9999px)

---

## 5. Elevation, Depth & Textures

- **Inset Rim Highlight (Dark Elements)**:
  `shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_14px_30px_rgba(0,0,0,0.13)]`
- **Inset Rim Highlight (Glass Elements)**:
  `shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]` or `shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]`
- **Floating Ambient Shadows**:
  - Hero Mirror: `shadow-[0_32px_80px_rgba(0,0,0,0.08)]`
  - Popover / Metric Cards: `shadow-[0_26px_60px_rgba(0,0,0,0.14)]`
  - Section Cards: `shadow-[0_18px_45px_rgba(0,0,0,0.08)]`
- **Texture Motifs**:
  - Hatched 45-degree linear patterns: `bg-[repeating-linear-gradient(135deg,#ff5a24_0,#ff5a24_1px,transparent_1px,transparent_0.45rem)]`
  - Dotted matrix grids: `[background-image:radial-gradient(circle,rgba(0,0,0,0.45)_1px,transparent_1.2px)] [background-size:1.6rem_1.2rem]`
  - Corner framing brackets: `border-r border-t border-white/45` (14x14px to 56x56px L-brackets)

---

## 6. Key UI Components & Patterns

1. **Category Tag / Signal Header**:
   - Square color block (`size-3 bg-[#ff5a24] shadow-[0_0_0_1px_rgba(255,90,36,0.18)]`) followed by uppercase tracking text (`AUTONOMOUS OPERATIONS`, `INTELLIGENT OPERATIONS`, etc.).
2. **Primary Action Buttons**:
   - Solid `#111111` background, white text, height `h-16`, inset top highlight `shadow-[inset_0_1px_0_rgba(255,255,255,0.14)]`, trailing icon (e.g. `arrow-right`).
3. **Secondary Action Buttons**:
   - Translucent `bg-white/20`, border `border-black/75`, dark text, height `h-16`, hover `hover:bg-white/60`.
4. **Signal Metric Card**:
   - Translucent rounded card (`bg-white/88 rounded-2xl p-6 backdrop-blur shadow-[0_26px_60px_rgba(0,0,0,0.16)]`).
   - Contains sparkline SVG path, large numeric stat (e.g. `98%`), and pulsing dot indicator (`size-2 bg-[#ff5a24] animate-pulse`).
5. **Operational Radar / Scanner Widget**:
   - Layered concentric rings with dashed border, crosshairs, central pulse ping, and rotating conic gradient scanner (`animate-[spin_4s_linear_infinite]`).
6. **Step-by-Step Flow Cards**:
   - Numbered header in Playfair Display (`01`, `02`, `03` in `#ff5a24` or white).
   - Connector arrows between sequence steps.
   - Micro-list items with mini status dots (`size-1.5 rounded-full bg-[#ff5a24]`).

---

## 7. Motion & Interaction Principles

- **Entrance Animation (`animationIn`)**:
  ```css
  @keyframes animationIn {
    0% {
      opacity: 0;
      transform: translateY(30px);
      filter: blur(8px);
    }
    100% {
      opacity: 1;
      transform: translateY(0);
      filter: blur(0px);
    }
  }
  ```
- **Scroll Reveal**: Triggered via `IntersectionObserver` adding `.animate` class to `.animate-on-scroll` elements.
- **Pulsing Live States**: `animate-pulse` on active sensor dots, `animate-ping` on critical radar targets.
- **Micro-Interactions**: Hover expansions (e.g. chart bars expanding `hover:h-8`), subtle scale and border brightness changes.

---

## 8. Icons & Assets

- **Icon Set**: Lucide Icons (`lucide-react` in Next.js / React).
- **Stroke Width**: `stroke-width="1.5"` for clean, technical elegance.
