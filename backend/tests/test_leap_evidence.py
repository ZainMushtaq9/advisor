"""Unit tests for the field-scoped LEAP evidence module.

Pure functions only: no database, no network, no status changes.
All example values are test fixtures, not registry observations.
"""

from __future__ import annotations

import pytest

from app.services.registry.leap_evidence import (
    NOT_FOUND_KEY,
    SOURCE_KEY,
    build_evidence_note,
    observation_to_evidence_row,
    parse_cuin,
    parse_leap_date,
    validate_observation,
)


def _agree_obs() -> dict:
    return {
        "company_id": 1,
        "ticker": "TEST",
        "query_wordings": ["Test Company Limited"],
        "query_that_found": "Test Company Limited",
        "incorporated_row": {
            "name": "TEST COMPANY LIMITED",
            "cuin": "0012345",
            "incorporation_date": "18-09-1993",
            "cro_city": "Karachi",
        },
        "organization_row": {
            "name": "TEST COMPANY LIMITED",
            "displayed_date": "09-18-3993",
        },
        "other_candidates": [],
        "outcome": "AGREE",
        "notes": "",
    }


def test_cuin_must_be_seven_digits() -> None:
    assert parse_cuin("0012345") == "0012345"
    for bad in ("12345", "12345678", "001234A", "", None, 12345):
        with pytest.raises(ValueError):
            parse_cuin(bad)


def test_leap_date_rejects_garbled_year() -> None:
    assert parse_leap_date("18-09-1993") == "18-09-1993"
    for bad in ("09-18-3993", "18/09/1993", "1993-09-18", "31-02-2020", ""):
        with pytest.raises(ValueError):
            parse_leap_date(bad)


def test_agree_observation_validates() -> None:
    assert validate_observation(_agree_obs(), "Test Company Limited") == []


def test_agree_requires_matching_name() -> None:
    obs = _agree_obs()
    obs["incorporated_row"]["name"] = "SOME OTHER COMPANY LIMITED"
    errors = validate_observation(obs, "Test Company Limited")
    assert any("must be DISAGREE" in e for e in errors)


def test_disagree_requires_differing_name() -> None:
    obs = _agree_obs()
    obs["outcome"] = "DISAGREE"
    errors = validate_observation(obs, "Test Company Limited")
    assert any("must be AGREE" in e for e in errors)


def test_not_found_must_not_carry_row() -> None:
    obs = _agree_obs()
    obs["outcome"] = "NOT_FOUND"
    errors = validate_observation(obs, "Test Company Limited")
    assert any("must not carry an incorporated_row" in e for e in errors)


def test_not_found_without_row_validates() -> None:
    obs = {
        "company_id": 1,
        "ticker": "TEST",
        "query_wordings": ["Test Company", "Test"],
        "query_that_found": None,
        "incorporated_row": None,
        "organization_row": None,
        "other_candidates": ["TESTING COMPANY LIMITED"],
        "outcome": "NOT_FOUND",
        "notes": "Candidates listed, none identifiable as the company.",
    }
    assert validate_observation(obs, "Test Company Limited") == []


def test_evidence_row_mapping_never_claims_sector_or_secp_key() -> None:
    row = observation_to_evidence_row(_agree_obs())
    assert row["source_key"] == SOURCE_KEY
    assert row["source_key"] != "secp"
    assert row["source_record_key"] == "0012345"
    assert row["observed_name"] == "TEST COMPANY LIMITED"
    assert row["observed_sector"] is None


def test_not_found_row_uses_not_found_key() -> None:
    obs = _agree_obs()
    obs["outcome"] = "NOT_FOUND"
    obs["incorporated_row"] = None
    obs["query_that_found"] = None
    row = observation_to_evidence_row(obs)
    assert row["source_record_key"] == NOT_FOUND_KEY
    assert row["observed_name"] is None


def test_evidence_note_carries_non_claims() -> None:
    note = build_evidence_note(_agree_obs())
    assert "CUIN recorded, not agreed" in note
    assert "not DPS listing status" in note
    assert "sector and ticker are not verifiable from LEAP" in note
    assert "changes no status" in note
    assert "3993" in note  # duplicate garbled row recorded, not hidden
