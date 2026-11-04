# ADR-001 — Frontend framework: Next.js + React + TypeScript

- **Status:** Accepted (Phase 1, revised fixed stack)
- **Date:** 2026-11-04
- **Supersedes:** The first draft of this ADR set (APScheduler-era draft); this version is the revised fixed-stack version.

## Context

PSX Intelligence AI needs a product web UI: dashboards, tables, and financial
charts over PSX data, with numbers that must match the backend exactly. The
fixed stack names Next.js / React / TypeScript / Tailwind / shadcn/ui. The
frontend must run on Node (v24.22.1 present on this machine, VERIFIED), cost
PKR 0, and not depend on any paid hosting.

## Decision

- **Framework:** Next.js (App Router) + React.
- **Language:** TypeScript throughout the frontend, including API response types
  derived from the FastAPI OpenAPI contract.
- **Styling/components:** Tailwind CSS + shadcn/ui (see Decisions §2.2 for the
  primitive caution: confirm Radix vs Base UI at setup — UNVERIFIED until then).
- **Charting:** TradingView Lightweight Charts only (Apache-2.0, VERIFIED),
  with the TradingView attribution + tradingview.com link kept on chart pages.

## Consequences

- Positive: server rendering + static generation for dashboard pages; typed
  API shapes catch backend/UI mismatches at build time; MIT licences, PKR 0.
- Negative: a full framework to learn vs plain React; Next.js major-version
  upgrades need care (App Router conventions change across majors — pin at setup).
- Constraint: the frontend never computes a financial number itself for display
  as truth; it renders series the backend computed (see ADR-010). The chart is a
  renderer, never a calculator or a data source.

## Alternatives considered

- Plain React + Vite — rejected: loses SSR/static without a Phase 1 gain.
- Vue/Nuxt, Angular — rejected: a second component model against the fixed
  React direction.
- Streamlit as product UI — rejected: couples presentation to the Python
  process; a prototype tool, not the product UI.
- MUI / Ant Design / Mantine as the component system — rejected: heavier
  runtime and/or a second design system; MUI X paid tiers excluded by PKR 0.
- Recharts / ECharts / Highcharts / Advanced Charts — rejected or excluded
  (see Comparison §3); Lightweight Charts is the single charting choice.

## Verification / open checks

- [ ] At Phase 2 setup: pin Next.js/React/TypeScript versions in the lockfile;
  record the shadcn/ui primitive actually installed; confirm Lightweight Charts
  major version and write chart code against that version only.
