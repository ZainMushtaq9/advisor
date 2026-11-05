/**
 * Mapping for GET /api/v1/market/status.
 *
 * The backend returns market_prices_total plus earliest/latest_trading_date
 * and counts_by_quality_status. There is no price_rows or trading_dates
 * field, so a card reading those names renders "—" and "no trading date"
 * even with 444 stored rows. This helper derives the display values both
 * snapshot cards use, so the two cards can never drift apart again.
 * Nothing here invents a value: a missing total stays missing, and the
 * quality badge is the single non-zero quality status (or "mixed").
 */

export interface MarketStatusResponse {
  market_prices_total?: number;
  securities_with_observations?: number;
  earliest_trading_date?: string | null;
  latest_trading_date?: string | null;
  counts_by_quality_status?: Record<string, number>;
  scope_note?: string;
}

export interface MarketStatusView {
  priceRows: number | undefined;
  tradingDates: string[];
  qualityStatus: string | undefined;
  scopeNote: string | undefined;
}

export function marketStatusView(data: MarketStatusResponse): MarketStatusView {
  const tradingDates = Array.from(
    new Set(
      [data.earliest_trading_date, data.latest_trading_date].filter(
        (d): d is string => Boolean(d),
      ),
    ),
  );
  const nonzero = Object.entries(data.counts_by_quality_status ?? {})
    .filter(([, n]) => (n ?? 0) > 0)
    .map(([status]) => status);
  return {
    priceRows: data.market_prices_total,
    tradingDates,
    qualityStatus:
      nonzero.length === 1
        ? nonzero[0]
        : nonzero.length > 1
          ? "mixed"
          : undefined,
    scopeNote: data.scope_note,
  };
}
