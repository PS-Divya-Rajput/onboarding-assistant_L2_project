---
name: Warm Editorial Dev
colors:
  surface: '#f4faff'
  surface-dim: '#d4dbe0'
  surface-bright: '#f4faff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eef4fa'
  surface-container: '#e8eff4'
  surface-container-high: '#e2e9ef'
  surface-container-highest: '#dce3e9'
  on-surface: '#161d21'
  on-surface-variant: '#414844'
  inverse-surface: '#2a3136'
  inverse-on-surface: '#ebf2f7'
  outline: '#717973'
  outline-variant: '#c1c8c2'
  surface-tint: '#3f6653'
  primary: '#012d1d'
  on-primary: '#ffffff'
  primary-container: '#1b4332'
  on-primary-container: '#86af99'
  inverse-primary: '#a5d0b9'
  secondary: '#904d00'
  on-secondary: '#ffffff'
  secondary-container: '#fe932c'
  on-secondary-container: '#663500'
  tertiary: '#002d1c'
  on-tertiary: '#ffffff'
  tertiary-container: '#00452e'
  on-tertiary-container: '#75b393'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c1ecd4'
  primary-fixed-dim: '#a5d0b9'
  on-primary-fixed: '#002114'
  on-primary-fixed-variant: '#274e3d'
  secondary-fixed: '#ffdcc3'
  secondary-fixed-dim: '#ffb77d'
  on-secondary-fixed: '#2f1500'
  on-secondary-fixed-variant: '#6e3900'
  tertiary-fixed: '#b1f0ce'
  tertiary-fixed-dim: '#95d4b3'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#0e5138'
  background: '#f4faff'
  on-background: '#161d21'
  surface-variant: '#dce3e9'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 44px
    fontWeight: '500'
    lineHeight: 52px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 26px
    fontWeight: '500'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-inline:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  code-block:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2.5rem
  margin-mobile: 1.25rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an editorial, high-performance workspace tailored for developer documentation, linting telemetry, and automated codebase migration workflows. Inspired by the tactical restraint of broadsheet typography and Swiss technical publishing, the interface marries deep technical clarity with the physical gravitas of ink on warm paper.

The aesthetic avoids playful tech tropes, neon accents, and decorative emojis entirely. Instead, it relies on structured rule lines, precise monospaced metadata, typographic contrast, and a calm tactile palette. The visual hierarchy communicates surgical speed, stability, and quiet authority—evoking the feeling of a fine reference manual combined with a high-throughput compilation engine.

## Colors

The color palette is built upon warm natural surfaces, high-contrast ink, deep conifers, and disciplined amber accents.

### Surface Tiers
- **Canvas Base (`#F5F4F0`)**: Warm alabaster paper tone for peripheral backgrounds and outer frame margins.
- **Card & Workspace Surface (`#FFFFFF`)**: Pure parchment white for elevated content sheets, reading areas, and interactive surfaces.
- **Subtle Well Surface (`#FBFBFA`)**: Soft cream tint for nested code blocks, technical tables, and recessed rule inspectors.

### Ink & Neutral Scale
- **Primary Ink (`#11181C`)**: Highest-contrast text for headlines, code tokens, and active rule names.
- **Secondary Ink (`#2D3748`)**: Balanced body text for prose, parameter documentation, and explanations.
- **Muted Slate (`#64748B`)**: Tertiary captions, file paths, line numbers, and keyboard shortcut glyphs.
- **Hairline Border (`#E4E4E7`)**: Crisp structural dividers, table grids, and input container borders.
- **Subtle Rule (`#F1F1EF`)**: Secondary dividers within content cards and dense tables.

### Accent & Semantic Roles
- **Primary Forest (`#1B4332`)**: Key navigation milestones, active sidebar items, primary commit buttons, and tool branding.
- **Forest Light (`#D8F3DC`)**: Soft background wash for resolved lint issues, passing rule states, and active tags.
- **Forest Mid (`#40916C`)**: Intermediate success indicators and secondary metric trends.
- **Proposal Amber (`#D97706`)**: Actionable linter suggestions, pending autofixes, warning badges, and focused cursor callouts.
- **Amber Light (`#FEF3C7`)**: Amber surface wash for diff previews and advisory notices.
- **Error Rust (`#B91C1C`)**: Critical syntax errors, fatal parse failures, and breaking schema alerts.

## Typography

The typographic system contrasts the literary warmth of `Newsreader` for section headlines and documentation titles with the utilitarian structure of `Inter` for prose and operational UI. `JetBrains Mono` handles all diagnostic codes, CLI parameters, rule identifiers, and metadata chips.

- **Prose Measure**: Maintain editorial text bodies between 60 to 75 characters per line for high-density readability.
- **Rule Titles**: Documentation rule headers pair an archival serif title with a monospace rule code badge (e.g., `E501`, `F401`) placed inline or as an overline kicker.
- **Numerals**: Numerical data within telemetry tables and diagnostic tallies must use tabular lining figures (`font-variant-numeric: tabular-nums`).
- **Code Blocks**: Inline code requires a subtle border and warm neutral tint to integrate smoothly into running text without visual harshness.

## Layout & Spacing

The layout operates on a deliberate three-tier fixed/fluid architecture anchored to an 8px spatial grid:

- **Desktop (1280px+)**: A three-pane layout featuring a fixed 260px table of contents/rules tree on the left, an 820px primary documentation reading and testing column in the center, and a 340px real-time AST inspector / telemetry sidebar on the right. Outer margins expand up to 40px (`space-xl`).
- **Tablet (768px – 1279px)**: Collapses the secondary inspector pane into an expandable bottom drawer. Left tree navigation switches to an overlay drawer. Center workspace fills available width with 24px margins.
- **Mobile (< 768px)**: Strict single-column stack with 20px edge margins. Code previews scroll horizontally with sticky line numbers.

Vertical rhythm adheres strictly to the scale: components utilize internal padding of `space-sm` (8px) for dense data rows and `space-md` (16px) for cards, while major section blocks divide across `space-xl` (40px) intervals.

## Elevation & Depth

This design system avoids heavy shadows, blur effects, and floating glass surfaces, choosing instead an ink-and-paper layered structure:

- **Level 0 (Base Canvas)**: Flat `#F5F4F0` background with zero elevation.
- **Level 1 (Card & Pane Sheet)**: Surface color `#FFFFFF` bounded by a 1px solid border (`#E4E4E7`). Layered with an ambient, diffused shadow: `0 1px 3px 0 rgba(17, 24, 28, 0.04), 0 1px 2px -1px rgba(17, 24, 28, 0.04)`.
- **Level 2 (Interactive Flyout / Dropdown)**: Raised parchment surface framed by `#E4E4E7` border with a targeted shadow: `0 4px 6px -1px rgba(17, 24, 28, 0.07), 0 2px 4px -2px rgba(17, 24, 28, 0.05)`.
- **Level 3 (Diagnostic Popovers & Command Palette)**: `#FFFFFF` surface framed by `#D1D5DB` with structural elevation: `0 12px 24px -4px rgba(17, 24, 28, 0.08), 0 4px 8px -2px rgba(17, 24, 28, 0.04)`.

Separation between sibling items in tables, trees, and lists is established through fine 1px hairline borders (`#F1F1EF`) rather than drop shadows.

## Shapes

The interface embraces a low-radius, architectural geometry reflecting the precision of linotype forms and technical blueprints.

- **Interactive Controls (Buttons, Inputs)**: `rounded` (4px / 0.25rem). Crisp, grounded edges that align cleanly with surrounding vertical grid rules.
- **Cards, Code Panels & Modals**: `rounded-lg` (8px / 0.5rem). Just enough curvature to detach from the base canvas while retaining sharp definition.
- **Badges, Rule Tags & AST Chips**: Strictly squared `rounded` (4px / 0.25rem) or 2px micro-radii. Avoid full pill shapes to maintain the dignified editorial demeanor.

## Components

### Buttons
- **Primary**: Solid Forest Green (`#1B4332`) background, crisp white text, 4px border radius. Hover state shifts to `#2D6A4F` with zero translate transitions. Active state settles into `#143527`.
- **Secondary**: Pure white surface, 1px border (`#E4E4E7`), text `#11181C`. Hover state introduces `#FBFBFA` surface tint and `#D1D5DB` border.
- **Amber Proposal Action**: Honey Amber (`#D97706`) background with white text, reserved for "Apply Autofix" or migration acceptance buttons.
- **Ghost/Tertiary**: No initial background or border; `#2D3748` text. Hover adopts `#F5F4F0` background.

### Input Fields & Search Bars
- Background `#FFFFFF`, 1px solid border `#E4E4E7`, 4px radius.
- Height: 36px for dense tooling search; 40px for global doc search.
- Focus state: Replaces outline with a precise 1px border in `#1B4332` paired with a 2px outer ring in `#D8F3DC` at 100% opacity (no blur).
- Code Inputs & Query Bars use `JetBrains Mono` at 13px with subtle line markers.

### Code Blocks & Diff Viewers
- Container surface is `#FBFBFA` bordered by `#E4E4E7`.
- Header bar: 32px height, `#F5F4F0` background, displaying file path in `label-sm` (`#64748B`) and language/engine badge.
- Gutter numbers: Monospace, `#94A3B8`, right-aligned, separated from code with a 1px solid hairline.
- Diff Additions: Subtle background `#D8F3DC` with dark green text (`#1B4332`).
- Diff Deletions: Subtle background `#FEE2E2` with dark red text (`#991B1B`).

### Badges & Rule Chips
- **Diagnostic Badges**: `JetBrains Mono` 11px uppercase. 
  - Lint Fix Available: `#FEF3C7` background, `#B45309` text, 1px `#FDE68A` border.
  - Safe / Pure: `#D8F3DC` background, `#1B4332` text, 1px `#B7E4C7` border.
  - Deprecated: `#F1F5F9` background, `#64748B` text, 1px `#E2E8F0` border.

### Cards & Inspectors
- `#FFFFFF` surface with 1px border (`#E4E4E7`).
- Card headers feature an editorial section title (`Newsreader`, 18px), optional metadata badges on the right, and a 1px bottom border before the card body.

### Selection Controls (Checkboxes & Radios)
- Checkboxes: 16x16px square with 3px radius, 1px solid `#CBD5E1`. Checked state fills `#1B4332` with a sharp geometric checkmark icon.
- Focus visible rings use a clean `#D8F3DC` bounding outline without drop shadow.