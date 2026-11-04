"""Deterministic matching for the Phase 4 registry.

Matching is deliberately narrow. A record matches an existing entity
only when a hard identifier agrees:

1. ISIN agrees (strongest), or
2. a stored identifier (type + value) agrees, or
3. the normalized ticker agrees AND the normalized company name agrees.

Ticker alone is NOT enough: tickers are reused after delisting and
renamed (ENGRO -> ENGROH is the verified PSX rename case). Name alone
is NOT enough: names collide across unrelated issuers.

Outcomes:
- "unique"    — exactly one candidate passes a rule.
- "none"      — no candidate passes any rule (new entity).
- "ambiguous" — two or more candidates pass, or the rules disagree
  (e.g. ticker agrees with company A but ISIN agrees with company B).
  Ambiguous records are kept original, marked PENDING_REVIEW, and
  NEVER auto-merged. A human (or a later verified source) resolves them.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.registry.normalization import (
    normalize_isin,
    normalize_name,
    normalize_ticker,
)


@dataclass(frozen=True)
class Candidate:
    """A pre-existing entity, as seen by the matcher (no ORM here,
    so this module is unit-testable without a database)."""

    entity_id: int
    ticker: str | None
    legal_name: str | None
    isin: str | None
    identifiers: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class MatchOutcome:
    outcome: str  # "unique" | "none" | "ambiguous"
    entity_id: int | None
    rule: str
    detail: str


def _safe_normalize(fn, value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return fn(value)
    except (ValueError, TypeError):
        return None


def match_record(
    *,
    ticker: str | None,
    legal_name: str | None,
    isin: str | None,
    identifiers: tuple[tuple[str, str], ...] = (),
    candidates: list[Candidate],
) -> MatchOutcome:
    """Deterministically match one source record against candidates."""
    norm_ticker = _safe_normalize(normalize_ticker, ticker)
    norm_name = _safe_normalize(normalize_name, legal_name)
    norm_isin = _safe_normalize(normalize_isin, isin)
    id_set = {(t.strip().upper(), v.strip().upper()) for t, v in identifiers}

    hits: dict[int, list[str]] = {}

    def hit(entity_id: int, rule: str) -> None:
        hits.setdefault(entity_id, []).append(rule)

    for cand in candidates:
        cand_isin = _safe_normalize(normalize_isin, cand.isin)
        if norm_isin and cand_isin and norm_isin == cand_isin:
            hit(cand.entity_id, "isin")
        cand_ids = {(t.strip().upper(), v.strip().upper()) for t, v in cand.identifiers}
        if id_set and (id_set & cand_ids):
            hit(cand.entity_id, "identifier")
        cand_ticker = _safe_normalize(normalize_ticker, cand.ticker)
        cand_name = _safe_normalize(normalize_name, cand.legal_name)
        if norm_ticker and cand_ticker and norm_ticker == cand_ticker:
            if norm_name and cand_name and norm_name == cand_name:
                hit(cand.entity_id, "ticker+name")
            elif norm_name is None or cand_name is None:
                # Name missing on one side: ticker alone is insufficient.
                pass
            else:
                # Same ticker, different name: a rename, reuse, or
                # conflict — never a silent match.
                hit(cand.entity_id, "ticker_conflict_name")

    if not hits:
        return MatchOutcome("none", None, "no_rule", "No candidate passed any match rule.")
    if len(hits) == 1:
        entity_id, rules = next(iter(hits.items()))
        if "ticker_conflict_name" in rules and len(rules) == 1:
            return MatchOutcome(
                "ambiguous",
                None,
                "ticker_conflict_name",
                f"Same ticker as entity {entity_id} but a different company name; "
                "treated as a possible rename/reuse, not a match.",
            )
        if "isin" in rules:
            rule = "isin"
        elif "identifier" in rules:
            rule = "identifier"
        else:
            rule = "ticker+name"
        return MatchOutcome("unique", entity_id, rule, f"Matched by {rule}.")
    return MatchOutcome(
        "ambiguous",
        None,
        "multiple_candidates",
        f"Multiple entities matched: {sorted(hits)}; manual review required.",
    )
