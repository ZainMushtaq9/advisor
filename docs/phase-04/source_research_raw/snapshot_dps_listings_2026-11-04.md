# Dated official-source snapshot — PSX Data Portal, Listing Status page (0 ROWS EXTRACTED)

- Source URL: https://dps.psx.com.pk/listings
- Source name: PSX Data Portal (DPS) — "Listing Status" page
- Fetched: 2026-11-04 12:56 PKT (page crawled 2026-11-04 07:56 UTC, per fetch header)
- Fetch method: text fetch only (browser.open). No live-browser visit, no sign-in, no form use.
- Row count extracted: 0 company/ticker/sector rows.

## What the fetched text actually showed

- Page title: "Listing Status - Pakistan Stock Exchange (PSX)".
- Index ticker strip only (e.g. KSE100 170,576.60, +2557.74 (1.52%); ALLSHR 102,501.48;
  KSE30 50,198.00; KMI30 244,843.73; plus BKTI, OGTI, KMIALLSHR, PSXDIV20, UPP9, NITPGI,
  NBPPGI, MZNPI, JSMFI, ACI, JSGBKTI, HBLTTI, MII30 values as fetched).
- Listing board/category labels only: "Listings, Main Board, GEM Board, Normal Counter"
  and "Non-Compliant Segment or Winding-Up Segment".
- A disclaimer: "Pakistan Stock Exchange (PSX) & CS Solutions (Pvt.) Limited (CS) do not
  guarantee the timeliness, accurateness, or completeness of any data or information on
  the website" (plus warranty/liability disclaimers; full text in the fetch).
- NO company-name, ticker, sector, or listing-status table rows appeared in the fetched text.

## Why 0 rows is NOT a finding that the site has no listing data

The DPS site is a JavaScript-driven portal. A text fetch does not execute its front-end
table rendering, so the absence of rows here means only: "no rows were extractable by
this text fetch on this date". The listing table (Main Board / GEM Board / Normal Counter /
Non-Compliant / Winding-Up) may render in a live browser session. That live-browser check
was NOT done by this worker (generic subagent, no live browser) and must be arranged by
the parent if a dated official DPS listing snapshot is required.

## Related DPS structure actually seen (same date, text fetch)

- DPS sitemap, https://dps.psx.com.pk/sitemap, fetched 2026-11-04 12:56 PKT, lists under
  "Companies": Listing Status (Normal Counter; Non-Compliant Segment or Winding-Up Segment),
  Circuit Breakers (Upper Cap; Lower Cap), Margin Eligible Securities, Aquisition/Loss of
  Shares [spelling as shown on the page]; under "Market": Today's Summary, Sector Overview,
  Stock Screener, Historical Data, Eligible Scrips, etc. No company rows are shown on the
  sitemap page itself either.
