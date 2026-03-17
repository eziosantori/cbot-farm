# UI Visual System

## Goal
Move the web app from a basic report viewer to a research workstation for strategy operations.

## Visual Direction
- Overall feel: `trading research workstation`
- Tone: calm, technical, high-signal
- Avoid: generic SaaS dashboard visuals, loud gradients, oversized shadows, purple-first accents

## Core Principles
- Show hierarchy clearly: operators must understand system state in a few seconds.
- Favor dense but readable information layouts over decorative empty space.
- Keep metrics, IDs, paths, and parameters visually distinct from prose.
- Use color semantically, not decoratively.

## Design Tokens
- Background: warm light neutral with subtle structure
- Surface: layered paper-like panels with restrained borders
- Primary accent: deep teal for actions and positive momentum
- Secondary accent: steel blue for navigation and neutral highlights
- Risk accent: controlled red for warnings and failures
- Typography:
  - UI/headings: `IBM Plex Sans`
  - Metrics/code/path values: `IBM Plex Mono`

## Layout Model
- Persistent shell with:
  - top status bar
  - left navigation rail
  - content canvas
- Navigation groups:
  - Observe
  - Build
  - Simulate
  - Govern

## Shared Components
- `AppShell`
- `PageHeader`
- `StatCard`
- `SurfaceCard`
- `Badge`
- `Table`
- chart panels

## Dashboard Direction
- Hero panel describing current lab state
- KPI strip for runs, manifests, workflow coverage, and API/index health
- Latest activity split into runs and ingestion
- Quick actions surfaced as first-class navigation blocks
- Trend chart framed as a performance signal, not a decorative widget

## Phased Delivery
1. Design tokens and layout shell
2. Dashboard refresh
3. Batch analytics refresh
4. Workflow board refresh
5. Intake / optimization / simulations polish

## Acceptance Criteria
- Navigation is persistent and consistent across routes.
- Main pages share a unified visual grammar.
- Dashboard communicates system state without reading raw tables first.
- New UI elements remain compatible with the existing API/data model.
