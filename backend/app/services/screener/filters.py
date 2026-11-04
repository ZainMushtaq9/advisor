"""Phase 20 pure filter evaluation.

No DB, no network, no SQL generation of any kind: the runner
loads stored rows into plain dicts and these functions decide
pass / fail / missing / not_applicable. User input never
becomes SQL — filter thresholds are validated against the
registry (known filter key, known kind, known operator) before
evaluation, and an unknown key, kind, or operator raises
ValueError instead of running.

Outcome vocabulary:
- "pass" / "fail": the stored value was compared and the
  threshold decision is recorded, with the value and its
  source in evidence.
- "missing": no stored value exists (MISSING_VALUE), or the
  value exists only as a NOT_CALCULABLE row (NOT_CALCULABLE
  for technical indicators). Missing outcomes are excluded
  from scoring — they are never treated as zero, and never
  treated as a fail.
- "not_applicable": the filter's sector applicability excludes
  the security (industrial-only filters on COMMERCIAL BANKS).
  Also excluded from scoring.

A percentile outcome always names its peer set: peer values
are the present values of the same field across the peer
universe, and percentile = 100 * (peers strictly below the
security's value) / (peers with any present value). A peer
set of size 1 yields percentile 0.0 with a degenerate-peer-set
flag in evidence; a peer set of size 0 yields "missing".
"""

from __future__ import annotations

from decimal import Decimal

from app.services.screener import FILTER_REGISTRY

OPERATORS = (">=", "<=", ">", "<", "==")
TECHNICAL_FILTERS = ("sma_5", "rsi_14")
INDUSTRIAL_ONLY_SECTORS_EXCLUDED = ("COMMERCIAL BANKS",)


def _compare(value: Decimal, op: str, threshold: Decimal) -> bool:
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == ">":
        return value > threshold
    if op == "<":
        return value < threshold
    if op == "==":
        return value == threshold
    raise ValueError(f"Unknown operator: {op!r}")


def validate_filter_entry(entry: dict) -> dict:
    """Validate one screen filter entry against the registry.

    Returns the normalised entry. Raises ValueError for an
    unknown filter key, an unsupported kind, an unknown
    operator, or a missing threshold — never silently drops
    or rewrites a filter."""
    key = entry.get("filter")
    if key not in FILTER_REGISTRY:
        raise ValueError(f"Unknown filter: {key!r}")
    spec = FILTER_REGISTRY[key]
    kind = entry.get("kind")
    if kind not in spec["kinds"]:
        raise ValueError(f"Filter {key!r} does not support kind {kind!r}")
    if kind == "presence":
        return {"filter": key, "kind": kind}
    op = entry.get("op")
    if op not in OPERATORS:
        raise ValueError(f"Filter {key!r} has unknown operator {op!r}")
    if "value" not in entry or entry["value"] is None:
        raise ValueError(f"Filter {key!r} needs a threshold value")
    return {"filter": key, "kind": kind, "op": op, "value": entry["value"]}


def _field_value(filter_key: str, data: dict) -> tuple[object | None, str, dict]:
    """Resolve a security's stored value for a filter.

    Returns (value, value_status, source_evidence) where
    value_status is "computed", "insufficient_inputs",
    "not_applicable", or "absent" (no stored row at all)."""
    if filter_key == "close_price":
        return (
            data.get("close_price"),
            ("computed" if data.get("close_price") is not None else "absent"),
            {"table": "market_prices", "trading_date": data.get("price_date")},
        )
    if filter_key == "volume":
        return (
            data.get("volume"),
            ("computed" if data.get("volume") is not None else "absent"),
            {"table": "market_prices", "trading_date": data.get("price_date")},
        )
    if filter_key == "price_present":
        return (
            data.get("close_price") is not None,
            "computed",
            {
                "table": "market_prices",
                "trading_date": data.get("price_date"),
            },
        )
    if filter_key == "volume_share_pct":
        return (
            data.get("volume_share_pct"),
            ("computed" if data.get("volume_share_pct") is not None else "absent"),
            {"table": "liquidity_observations", "metric_key": "volume_share_pct"},
        )
    if filter_key in (
        "roe_total",
        "roa",
        "net_margin",
        "gross_margin",
        "current_ratio",
        "receivables_days",
        "debt_to_equity",
    ):
        row = (data.get("fundamentals") or {}).get(filter_key)
        if row is None:
            return None, "absent", {"table": "fundamental_metric_values"}
        return (
            row.get("value"),
            row.get("status", "absent"),
            {
                "table": "fundamental_metric_values",
                "metric_key": filter_key,
                "period_end": row.get("period_end"),
                "row_id": row.get("row_id"),
            },
        )
    if filter_key == "pe_trailing":
        row = (data.get("valuations") or {}).get("multiples:pe_trailing")
        if row is None:
            return None, "absent", {"table": "valuations"}
        return (
            row.get("value"),
            row.get("status", "absent"),
            {
                "table": "valuations",
                "method": "multiples:pe_trailing",
                "period_note": row.get("period_note"),
            },
        )
    if filter_key == "dividend_per_share":
        return (
            data.get("dividend_per_share"),
            ("computed" if data.get("dividend_per_share") is not None else "absent"),
            {
                "table": "corporate_action_records",
                "dates_known": data.get("dividend_dates_known", False),
                "amount_note": data.get("dividend_amount_note"),
            },
        )
    if filter_key == "news_event_present":
        return (
            data.get("news_event_count", 0) > 0,
            "computed",
            {
                "table": "news_events",
                "linked_event_count": data.get("news_event_count", 0),
            },
        )
    if filter_key == "risk_flag_present":
        return (
            data.get("risk_flag_count", 0) > 0,
            "computed",
            {
                "table": "risk_flags",
                "flag_count": data.get("risk_flag_count", 0),
            },
        )
    if filter_key == "statement_age_days":
        return (
            data.get("statement_age_days"),
            ("computed" if data.get("statement_age_days") is not None else "absent"),
            {"table": "financial_statements", "period_end": data.get("statement_period_end")},
        )
    if filter_key in TECHNICAL_FILTERS:
        # Zero calculable rows exist (Phase 6). There is no
        # value to resolve, and none is invented.
        return None, "not_calculable", {"table": "technical_indicator_values"}
    raise ValueError(f"Unknown filter: {filter_key!r}")


def evaluate_filter(entry: dict, data: dict, peer_values: list | None = None) -> dict:
    """Evaluate one validated filter entry for one security.

    `data` is the runner-built security dict; `peer_values`
    is the list of present values for the same field across
    the peer universe (required for percentile kinds, ignored
    otherwise). Returns an outcome dict with outcome, reason,
    value, percentile (when applicable), and evidence."""
    key = entry["filter"]
    kind = entry["kind"]
    spec = FILTER_REGISTRY[key]
    evidence: dict = {
        "filter": key,
        "category": spec["category"],
        "unit": spec["unit"],
        "source": spec["source"],
        "kind": kind,
    }
    # Sector applicability is decided before any value lookup:
    # an industrial-only filter on a bank is not_applicable,
    # not missing.
    if spec["sector_applicability"] == "industrial_only" and (
        data.get("sector") in INDUSTRIAL_ONLY_SECTORS_EXCLUDED
    ):
        evidence["reason_detail"] = (
            "Industrial ratio semantics do not apply to "
            f"{data.get('sector')} (Phase 8 banking rule)."
        )
        return {
            "filter": key,
            "outcome": "not_applicable",
            "reason": "SECTOR_NOT_APPLICABLE",
            "value": None,
            "evidence": evidence,
        }
    value, value_status, source_evidence = _field_value(key, data)
    evidence.update(source_evidence)
    if key in TECHNICAL_FILTERS:
        evidence["reason_detail"] = (
            "Phase 6 holds 0 calculable technical values; no value exists to compare."
        )
        return {
            "filter": key,
            "outcome": "missing",
            "reason": "NOT_CALCULABLE",
            "value": None,
            "evidence": evidence,
        }
    if kind == "presence":
        # Presence semantics are uniform: a resolved absence
        # (no price row, no linked event, no flag, no action)
        # is a genuine FAIL of the presence condition within
        # stored data — not missing data. The coverage caveat
        # (e.g. actions loaded for 2 companies only) rides in
        # evidence, and the result is a NO_MATCH, never an
        # invented value and never a silent pass.
        if key == "dividend_per_share":
            passed = data.get("dividend_per_share") is not None
            evidence["value"] = data.get("dividend_per_share")
            evidence["coverage_note"] = (
                "Dividend actions are loaded for 2 companies "
                "only (HUBC, NML); absence means no stored "
                "action, not proof the company pays nothing."
            )
        else:
            passed = bool(value)
            evidence["value"] = value
        return {
            "filter": key,
            "outcome": "pass" if passed else "fail",
            "reason": "PASS" if passed else "FAIL_THRESHOLD",
            "value": evidence["value"],
            "evidence": evidence,
        }
    # Absolute / percentile kinds need a numeric value.
    if value is None:
        reason = "MISSING_VALUE"
        if value_status in ("insufficient_inputs", "not_applicable"):
            evidence["row_status"] = value_status
        return {
            "filter": key,
            "outcome": "missing",
            "reason": reason,
            "value": None,
            "evidence": evidence,
        }
    numeric = value if isinstance(value, Decimal) else Decimal(str(value))
    threshold = Decimal(str(entry["value"]))
    if kind == "absolute":
        passed = _compare(numeric, entry["op"], threshold)
        evidence["threshold"] = str(threshold)
        return {
            "filter": key,
            "outcome": "pass" if passed else "fail",
            "reason": "PASS" if passed else "FAIL_THRESHOLD",
            "value": numeric,
            "evidence": evidence,
        }
    if kind == "percentile":
        peers = [p for p in (peer_values or []) if p is not None]
        if not peers:
            evidence["reason_detail"] = "Peer set is empty: no present values."
            return {
                "filter": key,
                "outcome": "missing",
                "reason": "MISSING_VALUE",
                "value": numeric,
                "evidence": evidence,
            }
        peer_decimals = [p if isinstance(p, Decimal) else Decimal(str(p)) for p in peers]
        below = sum(1 for p in peer_decimals if p < numeric)
        percentile = (Decimal(below) / Decimal(len(peer_decimals))) * Decimal(100)
        evidence["peer_set_size"] = len(peer_decimals)
        if len(peer_decimals) == 1:
            evidence["degenerate_peer_set"] = True
        passed = _compare(percentile, entry["op"], threshold)
        return {
            "filter": key,
            "outcome": "pass" if passed else "fail",
            "reason": "PASS" if passed else "FAIL_THRESHOLD",
            "value": numeric,
            "percentile": percentile,
            "evidence": evidence,
        }
    raise ValueError(f"Unknown kind: {kind!r}")
