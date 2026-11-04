"""Phase 4 registry tests — offline, no real PostgreSQL, no network.

The importer is exercised against a small fake session that implements
only the SQLAlchemy query surface the importer uses (query/filter_by/
first/all/count, add/flush). Live-PostgreSQL behaviour is checked
separately by scripts/run_phase4_pg_check.py, which runs inside a
rolled-back transaction and is NOT part of this pytest suite.
"""

from __future__ import annotations

import pytest

from app.models.reference import Company, CompanyIdentifier, Security
from app.models.registry import RegistryEvidence
from app.services.registry import matching, normalization
from app.services.registry.importer import SourceRecord, import_records
from app.services.registry.matching import Candidate
from app.services.registry.reconciliation import reconcile


# ---------------------------------------------------------------- fake session
class _FakeQuery:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def filter_by(self, **kwargs) -> "_FakeQuery":
        rows = [
            r
            for r in self._rows
            if all(getattr(r, k, None) == v for k, v in kwargs.items())
        ]
        return _FakeQuery(rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self) -> list:
        return list(self._rows)

    def count(self) -> int:
        return len(self._rows)


class FakeSession:
    """Minimal in-memory stand-in for a SQLAlchemy session."""

    def __init__(self) -> None:
        self.store: dict[type, list] = {}
        self._next_id = 1

    def query(self, model):  # noqa: ANN001, ANN202
        return _FakeQuery(self.store.setdefault(model, []))

    def add(self, obj) -> None:  # noqa: ANN001
        if getattr(obj, "id", None) is None:
            obj.id = self._next_id
            self._next_id += 1
        self.store.setdefault(type(obj), []).append(obj)

    def flush(self) -> None:
        return None


# ---------------------------------------------------------------- normalization
def test_normalize_ticker_upper_and_strips_spaces() -> None:
    assert normalization.normalize_ticker(" ogdc ") == "OGDC"


def test_normalize_ticker_rejects_empty() -> None:
    with pytest.raises(ValueError):
        normalization.normalize_ticker("   ")


def test_normalize_name_strips_suffix_only_for_key() -> None:
    assert normalization.normalize_name("Engro Corporation Limited") == "ENGRO"
    assert normalization.normalize_name("Engro Corp.") == "ENGRO CORP"


def test_normalize_isin_validates_format() -> None:
    assert normalization.normalize_isin("pk0012345678") == "PK0012345678"
    with pytest.raises(ValueError):
        normalization.normalize_isin("not-an-isin")


# ---------------------------------------------------------------- matching
def _cand(entity_id: int, ticker: str, name: str, isin: str | None = None) -> Candidate:
    return Candidate(entity_id=entity_id, ticker=ticker, legal_name=name, isin=isin)


def test_match_ticker_plus_name_unique() -> None:
    out = matching.match_record(
        ticker="OGDC", legal_name="Oil & Gas Development Company Limited",
        isin=None, candidates=[_cand(1, "OGDC", "Oil and Gas Development Company Limited")],
    )
    assert out.outcome == "unique" and out.entity_id == 1


def test_match_ticker_alone_is_not_enough() -> None:
    out = matching.match_record(
        ticker="OGDC", legal_name="Some Other Company",
        isin=None, candidates=[_cand(1, "OGDC", "Oil and Gas Development Company Limited")],
    )
    assert out.outcome == "ambiguous"


def test_match_isin_wins() -> None:
    out = matching.match_record(
        ticker="XXXX", legal_name="Different Name",
        isin="PK0012345678",
        candidates=[_cand(1, "OGDC", "Oil and Gas Development Company Limited", "PK0012345678")],
    )
    assert out.outcome == "unique" and out.rule == "isin"


def test_match_multiple_candidates_ambiguous() -> None:
    out = matching.match_record(
        ticker="ABC", legal_name="ABC Company Limited", isin=None,
        candidates=[_cand(1, "ABC", "ABC Company"), _cand(2, "ABC", "ABC Company")],
    )
    assert out.outcome == "ambiguous"


def test_match_none_for_new_record() -> None:
    out = matching.match_record(ticker="NEW", legal_name="New Company", isin=None, candidates=[])
    assert out.outcome == "none"


# ---------------------------------------------------------------- importer
def _records() -> list[SourceRecord]:
    return [
        SourceRecord(ticker="OGDC", legal_name="Oil and Gas Development Company Limited",
                     sector_name="Oil & Gas Exploration", isin="PK0012345678"),
        SourceRecord(ticker="ENGROH", legal_name="Engro Holdings Limited",
                     sector_name="Fertilizer", isin="PK0098765432"),
    ]


def test_import_creates_and_is_idempotent() -> None:
    session = FakeSession()
    first = import_records(session, _records(), source_key="test_source",
                           source_display_name="Test Source")
    assert first.companies_created == 2 and first.securities_created == 2
    assert first.sectors_created == 2
    second = import_records(session, _records(), source_key="test_source",
                            source_display_name="Test Source")
    assert second.companies_created == 0 and second.securities_created == 0
    assert second.skipped_as_duplicate == 2
    assert len(session.query(Company).all()) == 2
    assert len(session.query(Security).all()) == 2


def test_import_never_verifies_on_success() -> None:
    session = FakeSession()
    import_records(session, _records(), source_key="test_source",
                   source_display_name="Test Source")
    assert all(c.status == "UNVERIFIED" for c in session.query(Company).all())


def test_import_second_source_promotes_to_partially_verified() -> None:
    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    import_records(session, _records(), source_key="source_b", source_display_name="Source B")
    assert all(c.status == "PARTIALLY_VERIFIED" for c in session.query(Company).all())


def test_import_official_source_alone_does_not_verify() -> None:
    # Audit H1: a lone official-source import must NOT mint VERIFIED
    # rows — the evidence row comes from the very record imported.
    session = FakeSession()
    import_records(session, _records(), source_key="psx_official",
                   source_display_name="PSX Official")
    assert all(c.status == "UNVERIFIED" for c in session.query(Company).all())


def test_import_official_plus_second_source_verifies() -> None:
    # VERIFIED now requires corroboration: >=2 distinct sources,
    # at least one official.
    session = FakeSession()
    import_records(session, _records(), source_key="psx_official",
                   source_display_name="PSX Official")
    import_records(session, _records(), source_key="source_b",
                   source_display_name="Source B")
    assert all(c.status == "VERIFIED" for c in session.query(Company).all())


def test_import_ambiguous_record_is_not_merged() -> None:
    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    result = import_records(
        session,
        [SourceRecord(ticker="OGDC", legal_name="Completely Different Company")],
        source_key="source_b", source_display_name="Source B",
    )
    assert result.pending_review == 1
    assert len(session.query(Company).all()) == 2  # no new company created


def test_import_rejects_bad_ticker_and_bad_isin() -> None:
    session = FakeSession()
    result = import_records(
        session,
        [
            SourceRecord(ticker="   ", legal_name="No Ticker Company"),
            SourceRecord(ticker="BAD", legal_name="Bad Isin Company", isin="XYZ"),
        ],
        source_key="source_a", source_display_name="Source A",
    )
    assert result.rejected == 2
    assert len(session.query(Company).all()) == 0


def test_import_rename_not_merged_on_name_alone() -> None:
    session = FakeSession()
    import_records(
        session, [SourceRecord(ticker="ENGRO", legal_name="Engro Corporation Limited")],
        source_key="source_a", source_display_name="Source A",
    )
    import_records(
        session, [SourceRecord(ticker="ENGROH", legal_name="Engro Corporation Limited")],
        source_key="source_a", source_display_name="Source A",
    )
    # ENGROH matched by name? No — ticker+name requires ticker agreement,
    # so the rename record is a NEW security in this strict model, and
    # the old one is untouched. The test pins that behaviour: renames
    # are never silently merged on name alone.
    assert len(session.query(Security).all()) == 2


def test_import_isin_match_name_disagreement_flags_pending_review() -> None:
    # Audit M1: ISIN match with a different name is flagged, not merged.
    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    import_records(
        session,
        [SourceRecord(ticker="OTHER", legal_name="Totally Different Name",
                      isin="PK0012345678")],
        source_key="source_b", source_display_name="Source B",
    )
    companies = session.query(Company).all()
    assert len(companies) == 2  # no new company created
    flagged = [c for c in companies if c.status == "PENDING_REVIEW"]
    assert len(flagged) == 1


def test_import_conflict_does_not_change_ticker() -> None:
    # Audit M2: a conflicting import must not mutate the ticker or
    # write symbol history before marking CONFLICTED.
    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    result = import_records(
        session,
        [SourceRecord(ticker="OGDC", legal_name="Oil and Gas Development Company Limited",
                      isin="PK0099999999")],
        source_key="source_b", source_display_name="Source B",
    )
    assert result.conflicts == 1
    securities = session.query(Security).all()
    assert len(securities) == 2  # no new security created
    ogdc = [s for s in securities if s.ticker == "OGDC"][0]
    assert ogdc.status == "CONFLICTED"
    assert ogdc.isin == "PK0012345678"  # stored ISIN unchanged


def test_import_ambiguous_reimport_does_not_duplicate_report() -> None:
    # Audit M3: quality reports are de-duplicated on re-import.
    from app.models.governance import DataQualityReport

    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    bad = [SourceRecord(ticker="OGDC", legal_name="Completely Different Company")]
    import_records(session, bad, source_key="source_b", source_display_name="Source B")
    import_records(session, bad, source_key="source_b", source_display_name="Source B")
    reports = [r for r in session.query(DataQualityReport).all()
               if r.issue_type == "ambiguous_registry_record"]
    assert len(reports) == 1


def test_import_listing_status_delisted_is_stored() -> None:
    # Audit M4: a stated delisted status is stored, not dropped.
    session = FakeSession()
    import_records(
        session,
        [SourceRecord(ticker="GONE", legal_name="Gone Company Limited",
                      listing_status="delisted")],
        source_key="source_a", source_display_name="Source A",
    )
    company = session.query(Company).all()[0]
    assert company.status == "DELISTED"


def test_import_matched_reimport_stores_new_identifiers() -> None:
    # Audit M5: identifiers on a matched re-import are stored.
    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    import_records(
        session,
        [SourceRecord(ticker="OGDC", legal_name="Oil and Gas Development Company Limited",
                      isin="PK0012345678",
                      identifiers=(("PSX_CODE", "0820"),))],
        source_key="source_a", source_display_name="Source A",
    )
    identifiers = session.query(CompanyIdentifier).all()
    assert ("PSX_CODE", "0820") in [(i.identifier_type, i.identifier_value)
                                     for i in identifiers]


def test_verification_ignores_empty_observed_name() -> None:
    # Audit LOW: an evidence row with no observed name never counts
    # as agreeing with the stored name.
    from app.services.registry.verification import apply_verification_rules

    session = FakeSession()
    import_records(session, _records(), source_key="source_a", source_display_name="Source A")
    company = session.query(Company).all()[0]
    session.add(RegistryEvidence(
        entity_type="company", entity_id=company.id, source_key="source_b",
        source_record_key="OGDC", observed_name=None, observed_sector=None,
    ))
    apply_verification_rules(session, company_id=company.id)
    assert company.status == "UNVERIFIED"


# ---------------------------------------------------------------- reconciliation
def test_reconcile_without_snapshot_makes_no_coverage_claim() -> None:
    session = FakeSession()
    session.add(Security(company_id=1, ticker="OGDC", status="UNVERIFIED"))
    report = reconcile(session, None)
    assert report.coverage_ratio is None
    assert report.registry_tickers == 1


def test_reconcile_malformed_snapshot_raises_clearly() -> None:
    # Audit LOW: a malformed snapshot must raise ValueError with a
    # clear message, not KeyError/AttributeError deep in the loader.
    import json
    import tempfile

    from app.services.registry.reconciliation import load_snapshot

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"source": "x"}, f)
        path = f.name
    with pytest.raises(ValueError, match="tickers"):
        load_snapshot(path)


def test_reconcile_reports_missing_and_extra() -> None:
    session = FakeSession()
    session.add(Security(company_id=1, ticker="OGDC", status="UNVERIFIED"))
    session.add(Security(company_id=2, ticker="EXTRA", status="UNVERIFIED"))
    report = reconcile(
        session,
        {"source": "test_snapshot", "snapshot_date": "2026-11-04",
         "tickers": ["OGDC", "MISSING"], "dropped": 0},
    )
    assert report.matched == 1
    assert report.missing_from_registry == ["MISSING"]
    assert report.extra_in_registry == ["EXTRA"]
    assert report.coverage_ratio == 0.5
