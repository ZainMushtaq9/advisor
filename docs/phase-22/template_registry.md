# Phase 22 — Template Registry and Report Schema

## Templates (8)

| Key | Title | Audience | Sections |
|---|---|---|---|
| company_dossier | Company Dossier | internal_research | executive_summary, thesis, counter_thesis, financial_snapshot, valuation, risks, catalysts, uncertainty, monitoring, disclosures |
| earnings_update | Earnings Update | internal_research | executive_summary, results, thesis, counter_thesis, risks, uncertainty, monitoring, disclosures |
| valuation_report | Valuation Report | internal_research | executive_summary, methods, scenarios, thesis, counter_thesis, risks, uncertainty, disclosures |
| sector_outlook | Sector Outlook | internal_research | executive_summary, coverage, thesis, counter_thesis, risks, uncertainty, monitoring, disclosures |
| event_brief | Event Brief | internal_research | executive_summary, event, thesis, counter_thesis, risks, uncertainty, monitoring, disclosures |
| portfolio_review | Portfolio Review | internal_research | executive_summary, holdings, exclusions, comparison, thesis, counter_thesis, risks, uncertainty, disclosures |
| risk_report | Risk Report | internal_research | executive_summary, metrics, controls, stress, thesis, counter_thesis, uncertainty, disclosures |
| market_overview | Market Overview | internal_research | executive_summary, breadth, macro, screens, decisions, alerts, thesis, counter_thesis, risks, uncertainty, disclosures |

Every template ends with a `disclosures` section carrying the
methodology, the source-table list, and the full disclaimer
(internal research only; not investment advice; no price
target; no trade recommendation; not published externally).

## Report schema

- `report_templates`: template_key, version (`v1`),
  title, audience, sections (JSON list of key/title),
  methodology, disclosure. Unique on (template_key, version).
- `reports`: template_id, template_key, template_version,
  subject_type (company / sector / macro_event / news_event
  / portfolio / market), subject_key, subject_label,
  report_date, data_cutoff_date, price_date (nullable),
  audience, status (DRAFT at generation; APPROVED or
  REJECTED only via the CLI), version_number, supersedes_id,
  is_current, snapshot (methodology + section list),
  provenance (quality_status etc.).
- `report_sections`: report_id, section_key, title,
  position (template order), body_markdown.
- `report_figures`: report_id, figure_key, label, value
  (Numeric 24,6, nullable), value_text (nullable), unit,
  computation_status, figure_kind, source_table,
  source_row_ids (JSON), source_note, quality_status.
  Rule: a computed figure carries exactly one value form; a
  non-computed figure carries neither.
- `report_warnings`: report_id, warning_kind (stale /
  missing / unknown_date / gate / risk_flag / coverage /
  scheduled / not_calculable), message, source_table,
  source_row_ids.
- `report_exports`: report_id, export_format (markdown /
  html / pdf), content_hash (SHA-256), storage_location.
  Markdown/HTML live under `docs/phase-22/reports/`; PDFs
  under gitignored `storage/research_reports/`.

## Subject keys

- Company reports: ticker (`HUBC`, `NML`, `OGDC`).
- Sector outlooks: sector name exactly as stored
  (`POWER GENERATION & DISTRIBUTION`, `TEXTILE COMPOSITE`,
  `OIL & GAS EXPLORATION COMPANIES`).
- Event briefs: `macro:YYYY-MM-DD:<event_type>` (e.g.
  `macro:2026-10-26:mpc_meeting`) or
  `news:<ticker>:<event_type substring>` (e.g.
  `news:HUBC:earning`, matched case-insensitively).
- Portfolio reviews: simulated portfolio name (e.g.
  `ew_statements_3_balanced`).
- Risk reports: ticker, or `MARKET` for market-level rows.
- Market overview: subject `market` (no subject argument).

## Header fields on every report

Report date 2026-11-04, data cut-off 2026-11-04, price date
2026-11-03, audience internal_research, status DRAFT.
Currency PKR throughout; statement amounts in Rs '000s
unless a figure note says otherwise.
