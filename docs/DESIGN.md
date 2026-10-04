---
version: alpha
name: Axisflow AI Operations Template
description: A high-density, professional operational dashboard and landing page focusing on AI-driven workflows, utilizing a mix of serif elegance and brutalist precision.
colors:
  primary: "#ff5a24"
  primary-dark: "#ff6330"
  background-tan: "#f6f5f2"
  background-dark: "#111111"
  text-main: "#090909"
  text-muted: "#6a6a6a"
  surface-light: "#ffffff"
  border-light: "rgba(0,0,0,0.1)"
typography:
  headings: "'Playfair Display', Georgia, serif"
  body: "'Inter', ui-sans-serif, system-ui, sans-serif"
  base-size: "16px"
  h1: "text-5xl to text-7xl"
spacing:
  section-py: "5rem to 6rem"
  container-max: "112rem"
rounded:
  default: "0.5rem"
  large: "1rem"
  card: "1.5rem"
  pill: "9999px"
components:
  primary-button: "{colors.background-dark} text-white shadow-inset-white-10"
  secondary-button: "bg-white/20 border-black/75"
  card: "bg-white/35 border-black/10 shadow-sm backdrop-blur"
---

## Overview
Axisflow is characterized by a sophisticated "Operational Elegance" aesthetic. It combines high-fidelity data visualization components with classical serif typography (Playfair Display) to create a sense of authoritative reliability. The layout is dense but organized, utilizing a radial gradient background that transitions from off-white to soft tan. It uses a signature orange accent (#ff5a24) for "signals" and critical path actions.

## Colors
- **Base Foundation**: The primary background is `#f6f5f2` with a radial gradient starting from `rgba(255,255,255,0.96)` at the top center.
- **Accent Color**: `#ff5a24` (Safety Orange) is used for active states, indicators, and pulse animations.
- **Dark Surfaces**: `#111111` or `#1b1c1b` are used for high-contrast cards and primary CTA buttons.
- **Text Hierarchy**: Pure black `#000000` for titles, `#252525` for subtext, and `#7a7a7a` for metadata.

## Typography
- **Display Serif**: Playfair Display (Medium, Italic) is used for H1 and H2 headings to convey prestige. It often features italicized accent words in the primary orange color.
- **Functional Sans**: Inter is the workhorse font for navigation, buttons, and data readouts, focusing on legibility at small sizes.
- **Formatting**: Tracking is tight for headings (`tracking-tight`) but wide for branding (`tracking-[0.22em]`) and labels (`tracking-wide`).

## Layout
- **Max Width**: Content is constrained to a `max-w-[112rem]` container.
- **Grid Systems**:
  - Hero: 2-column grid (`0.77fr_1.23fr`) at large screens.
  - Feature Sections: 3-column or 5-column grids with specific gap patterns (`gap-7` or `gap-10`).
- **Padding**: Standardized responsive padding (`px-6` mobile, `px-10` tablet, `px-16` desktop).

## Elevation & Depth
- **Inward Depth**: Extensive use of `shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]` to create a "pressed" or premium material effect on dark buttons and cards.
- **Soft Shadows**: Cards use large, diffused shadows like `shadow-[0_32px_80px_rgba(0,0,0,0.08)]` to float above the tan background.
- **Glassmorphism**: Surfaces frequently use `bg-white/35` or `bg-white/88` combined with `backdrop-blur` for layered visibility.

## Shapes
- **Geometric Precision**: Perfect circles for radar-like visualizations.
- **Corner Radii**:
  - UI Buttons: `rounded-md` (8px).
  - Major Sections/Large Cards: `rounded-[2.7rem]` or `rounded-2xl`.
  - Status Indicators: Perfect squares or `rounded-full` dots.
- **Graphic Patterns**: Repeating linear gradients are used to create "hatched" textures on cards and buttons.

## Components
- **Navigation Bar**: Transparent background, large letter-spaced brand text, and a distinct primary CTA with internal inset shadows.
- **Action Buttons**: Large (h-16), wide (sm:w-56) buttons with internal spacing for icons (gap-10).
- **Signal Cards**: Miniature data visualizations containing SVG sparklines, percentage readouts, and pulsing status dots.
- **Feature Articles**: Bordered containers (`border-black/15`) with radial gradient overlays to highlight specific corners or content areas.
- **Radar Visual**: A complex layered component of concentric circles, dashed borders, and a spinning conic gradient scanner.

## Page Sections
### Navigation
- **Structure**: Horizontal flexbox with logo on left, centered links, and right-aligned CTA.
- **Interactions**: Hover color shift to orange for nav links.

### Hero Section
- **Left Column**: High-impact Playfair typography with a gradient-text italicized accent. Includes a square orange indicator label ("AUTONOMOUS OPERATIONS").
- **Right Column**: An "Operational Mirror" surface—a large rounded container featuring the radar scanner, a signal health sparkline (98%), and a bar chart for active automations.

### Feature Grid (Intelligent Operations)
- **Composition**: A vertical stack of three feature blocks.
- **Visuals**: One large dark card with a concentric circular "predictive" diagram, and two smaller stacked cards on the right (Flow Coordination and Live Coverage) featuring skeletal UI diagrams and scanned patterns.

### How It Works (Step-by-Step)
- **Structure**: A 1-2-3 sequence connected by horizontal SVG arrows.
- **Visual Content**:
  - Step 1: Signal capture with nested list of status items (Monitoring, Alerts, etc.).
  - Step 2: Automated response with a central rotating gear/rhombus icon.
  - Step 3: Align Teams showing a mini-dashboard with bar charts, circular progress, and user avatars.

### Pricing
- **Design**: Three distinct tiers. The central "Growth" plan is highlighted with a primary orange border and a "Most Popular" floating badge.
- **Features**: Checklist items with circular border-styled checkmarks and price readouts in large numeric display.

## Motion & Interaction
- **Entrance**: An `animationIn` keyframe (translateY from 20px, opacity 0 to 1) applied to major sections using an `IntersectionObserver` triggered on scroll.
- **Pulsing Icons**: Status dots and the hero's italicized text use `animate-pulse` or `animate-ping` for "live" signal cues.
- **Spinning Radar**: A constant `animate-[spin_4s_linear_infinite]` on the conic gradient scanner in the hero visual.
- **Hover Effects**: Sub-bars in charts increase height on hover (`hover:h-8`).

## Do's and Don'ts
- **Do**: Use high-contrast between pure black backgrounds and primary orange accents.
- **Do**: Maintain the 1px inset white shadow on all dark interactive elements.
- **Don't**: Use standard sans-serif for headings; the Playfair Display serif is essential for the brand's "Operations" tone.
- **Don't**: Over-animate; stick to the evidenced pulsing dots and subtle entry reveals.

## Accessibility
- **Labels**: ARIA labels are used for navigation toggles ("Open menu") and brand links ("Axisflow").
- **Contrast**: High contrast ratios on dark buttons (white text on black) and clear status indicators (orange dots).
- **Structure**: Use of semantic `<main>`, `<header>`, `<section>`, and `<article>` tags for logical screen reader traversal.

## Assets
- **Icons**: Lucide Icons (menu, arrow-right, check, etc.) - `https://unpkg.com/lucide@latest/dist/umd/lucide.min.js`
- **Typography**: Inter and Playfair Display - `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:ital,wght@0,500;1,500&display=swap`
- **Framework**: Tailwind CSS - `https://cdn.tailwindcss.com`

### Exported Codebase Asset Inventory
1. embed: https://fonts.gstatic.com
   Context: index.html: markup attribute; index.html: absolute url literal
2. embed: https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&amp;family=Playfair+Display:ital,wght@0,500;1,500&amp;display=swap
   Context: index.html: markup attribute; index.html: absolute url literal
3. other: http://www.w3.org/2000/svg
   Context: index.html: absolute url literal
