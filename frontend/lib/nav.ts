export interface NavItem {
  href: string;
  label: string;
  /** Short description used on the home page and for screen readers. */
  description: string;
}

/** Single source of truth for primary navigation (foundation routes only). */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", description: "Project foundation overview." },
  {
    href: "/dashboard",
    label: "Dashboard",
    description: "Market overview shell — no data yet.",
  },
  {
    href: "/companies",
    label: "Companies",
    description: "Company directory shell — no data yet.",
  },
  {
    href: "/market",
    label: "Market",
    description: "Daily OHLCV for snapshot securities, from validated observations only.",
  },
  {
    href: "/indicators",
    label: "Indicators",
    description: "Deterministic indicator coverage; every value explained or marked NOT_CALCULABLE.",
  },
  {
    href: "/research",
    label: "Research",
    description: "Research workspace shell — no data yet.",
  },
  {
    href: "/portfolio",
    label: "Portfolio",
    description: "Portfolio workspace shell — no data yet.",
  },
  {
    href: "/alerts",
    label: "Alerts",
    description: "Alerts workspace shell — no data yet.",
  },
  {
    href: "/admin",
    label: "Admin",
    description: "Operator workspace shell — no data yet.",
  },
];
