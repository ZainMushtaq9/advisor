export interface NavItem {
  href: string;
  label: string;
  /** Short description used on the home page and for screen readers. */
  description: string;
}

/** Single source of truth for primary navigation (Phase 23 product IA). */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", description: "Project overview and live status." },
  {
    href: "/dashboard",
    label: "Dashboard",
    description: "Market overview, macro regime, alerts and decisions at a glance.",
  },
  {
    href: "/companies",
    label: "Companies",
    description: "Registry of 470 Main Board / Normal Counter companies, searchable.",
  },
  {
    href: "/market",
    label: "Market",
    description: "Daily OHLCV snapshot for 2026-11-03, plus breadth and liquidity.",
  },
  {
    href: "/securities",
    label: "Securities",
    description: "Security directory: tickers, classes and registry quality.",
  },
  {
    href: "/news",
    label: "News",
    description: "Seed events from stored rows only; live collection is Terms-gated.",
  },
  {
    href: "/fundamentals",
    label: "Fundamentals",
    description: "Statement-derived ratios and health for HUBC, NML and OGDC.",
  },
  {
    href: "/valuation",
    label: "Valuation",
    description: "Seventeen valuation methods; only computable ones carry values.",
  },
  {
    href: "/macro",
    label: "Macro",
    description: "SBP/PBS indicators, regime, events and company exposures.",
  },
  {
    href: "/indicators",
    label: "Technical",
    description: "Deterministic indicator coverage; every value explained or marked NOT_CALCULABLE.",
  },
  {
    href: "/forecasts",
    label: "Forecasts",
    description: "Forecast assessments — all abstained on the current single-date series.",
  },
  {
    href: "/risk",
    label: "Risk",
    description: "Risk metrics, controls, stress results and review-only flags.",
  },
  {
    href: "/portfolio",
    label: "Portfolio",
    description: "SIMULATED portfolios on hypothetical capital — never real holdings.",
  },
  {
    href: "/screener",
    label: "Screener",
    description: "Filter results over stored rows — not opportunities or recommendations.",
  },
  {
    href: "/alerts",
    label: "Alerts",
    description: "In-app notifications only; no external message is ever sent.",
  },
  {
    href: "/reports",
    label: "Reports",
    description: "Research reports — all DRAFT, none approved, none published.",
  },
  {
    href: "/research",
    label: "Research",
    description: "Decisions, backtests, orchestration and grounded document search.",
  },
  {
    href: "/admin",
    label: "Admin",
    description: "Backend health and endpoint status. No credentials are shown.",
  },
];
