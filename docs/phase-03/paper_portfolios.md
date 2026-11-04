# Phase 3 — Paper Portfolios

## Tables

portfolios (user_id, name, portfolio_type default 'paper',
currency default 'PKR') + portfolio_holdings (portfolio_id,
security_id, quantity, average_cost, valid_from, valid_to).

## Rules

1. **Paper-trading ONLY.** No brokerage account identifiers, no
   broker API fields, no order path, no real trades — anywhere in
   the schema (verified by a column-name test: no broker*,
   api_key, password or secret columns on portfolios or companies).
2. **Holdings reference securities.id, never a bare ticker.**
   A rename (symbol_history) therefore cannot corrupt a holding.
3. **Current state + history-ready shape.** The current holding
   row is mutable, but every change is audit-logged (audit_logs),
   and valid_from/valid_to exist so full holding history is an
   additive change (new row per change), not a redesign.
4. **Simulated is separate from real.** Any future real-trading
   feature would be a separate, separately approved design. Nothing
   in Phase 3 may be read as a trading capability.
5. **No valuation is stored as a holding fact.** A holding's
   quantity and average cost are facts; its current market value
   is a derived query over market_prices at a stated date, never
   a stored number that goes stale silently.
