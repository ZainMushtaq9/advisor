"""Phase 10 macro/sector tests (pure: no real database, no network).

Hand-checked expectations:
- Point-in-time: the SBP policy rate decision published 2026-10-26 is
  NOT known at 2026-10-25 and IS known at 2026-10-27; a PBS homepage
  value with no publication date falls back to its collection date.
- Vintage revision: revising an observation keeps the old row (flipped
  to not-current) and appends a new row with version + 1 and
  supersedes_id; revising a missing grain raises.
- Registry discipline: every VERIFIED observation has a documented
  cross-check; every exposure cites statement evidence (never sector
  membership); HBL has no exposure rows; the regime assessment assigns
  exactly one label and records why the others were not assigned.
- Nothing is zero-filled: an unknown indicator at a date returns None.
"""

from __future__ import annotations

import pytest

from app.services.macro_analysis import (
    CROSS_CHECKS,
    EXPOSURES,
    HBL,
    INDICATORS,
    NOT_STORED,
    OBSERVATIONS,
    REGIME_ASSESSMENT,
    SECTOR_PROFILES,
    formulas,
)


def _row(
    code, obs_date, value, source_ts=None, collected="2026-11-04", current=True, version=1, rid=1
):
    return {
        "id": rid,
        "indicator_code": code,
        "observation_date": obs_date,
        "value": value,
        "source_timestamp": source_ts,
        "collected_at": collected,
        "is_current": current,
        "version_number": version,
    }


# ---------------------------------------------------------------------------
# Point-in-time retrieval
# ---------------------------------------------------------------------------


def test_policy_rate_not_known_before_publication():
    rows = [_row("sbp_policy_rate", "2026-10-27", "12.00", source_ts="2026-10-26")]
    assert formulas.point_in_time(rows, "2026-10-25") is None


def test_policy_rate_known_on_effective_date():
    rows = [_row("sbp_policy_rate", "2026-10-27", "12.00", source_ts="2026-10-26")]
    found = formulas.point_in_time(rows, "2026-10-27")
    assert found is not None and found["value"] == "12.00"


def test_point_in_time_picks_latest_public_observation():
    rows = [
        _row("cpi_mom", "2026-09-30", "1.3", source_ts="2026-10-02", rid=1),
        _row("cpi_mom", "2026-10-31", "1.1", source_ts="2026-11-02", rid=2),
    ]
    assert formulas.point_in_time(rows, "2026-10-15")["value"] == "1.3"
    assert formulas.point_in_time(rows, "2026-11-04")["value"] == "1.1"


def test_point_in_time_falls_back_to_collection_date():
    # PBS homepage values carry no publication date: provably public
    # only from collection.
    rows = [_row("gdp_growth_fy", "2026-06-30", "3.65", source_ts=None, collected="2026-11-04")]
    assert formulas.point_in_time(rows, "2026-11-03") is None
    assert formulas.point_in_time(rows, "2026-11-04")["value"] == "3.65"


def test_point_in_time_ignores_non_current_rows():
    rows = [
        _row("cpi_yoy", "2026-09-30", "10.3", source_ts="2026-10-26", current=False, rid=1),
    ]
    assert formulas.point_in_time(rows, "2026-11-04") is None


def test_absent_indicator_returns_none_never_zero():
    assert formulas.point_in_time([], "2026-11-04") is None
    assert formulas.current_value([]) is None


# ---------------------------------------------------------------------------
# Vintage revision
# ---------------------------------------------------------------------------


def test_revision_preserves_old_row_and_links_new():
    rows = [_row("lsm_growth", "2026-08-31", "1.85", source_ts=None, collected="2026-11-04")]
    new_rows, new_row = formulas.revise(
        rows, "lsm_growth", "2026-08-31", "1.90", "2026-11-10", "2026-11-10"
    )
    assert len(new_rows) == 2
    old = [r for r in new_rows if r["id"] == 1][0]
    assert old["is_current"] is False
    assert old["value"] == "1.85"  # never edited
    assert new_row["value"] == "1.90"
    assert new_row["version_number"] == 2
    assert new_row["supersedes_id"] == 1
    assert new_row["is_current"] is True
    assert formulas.current_value(new_rows)["value"] == "1.90"


def test_revision_of_missing_grain_raises():
    with pytest.raises(ValueError):
        formulas.revise([], "lsm_growth", "2026-08-31", "1.90", None, "2026-11-10")


# ---------------------------------------------------------------------------
# Registry discipline
# ---------------------------------------------------------------------------


def test_every_registered_indicator_has_a_name_unit_frequency():
    for code, meta in INDICATORS.items():
        assert meta["name"] and meta["unit"] and meta["frequency"] and meta["publisher"]


def test_every_verified_observation_has_a_cross_check():
    for obs in OBSERVATIONS:
        assert obs["indicator_code"] in INDICATORS
        if obs["quality_status"] == "VERIFIED":
            assert obs["indicator_code"] in CROSS_CHECKS
            assert CROSS_CHECKS[obs["indicator_code"]]
        else:
            assert obs["indicator_code"] not in CROSS_CHECKS


def test_observation_counts():
    verified = [o for o in OBSERVATIONS if o["quality_status"] == "VERIFIED"]
    assert len(OBSERVATIONS) == 12
    assert len(verified) == 6


def test_no_observation_is_zero_filled():
    for obs in OBSERVATIONS:
        assert obs["value"] not in (None, "")
        assert float(obs["value"]) != 0 or obs["indicator_code"] == "spi_wow"


def test_every_exposure_cites_statement_evidence():
    for exp in EXPOSURES:
        assert exp["evidence_type"] == "statement_line_item"
        assert exp["evidence_ref"]
        assert "sector_membership" not in exp["evidence_type"]
    assert len(EXPOSURES) == 6


def test_hbl_has_no_exposure_rows():
    # Exposures are seeded by ticker (never by surrogate company id).
    assert all(exp["ticker"] != HBL for exp in EXPOSURES)


def test_sector_profiles_cover_four_sectors():
    sectors = {p["sector_id"] for p in SECTOR_PROFILES}
    assert sectors == {16, 8, 36, 4}
    assert all(p["metric_key"].startswith("macro:") for p in SECTOR_PROFILES)
    assert len(SECTOR_PROFILES) == 12


def test_regime_assigns_one_label_and_records_rejections():
    assert REGIME_ASSESSMENT["regime_label"] == "tightening"
    rejected = REGIME_ASSESSMENT["evidence"]["not_assigned"]
    assert set(rejected) == {
        "disinflation",
        "external_pressure",
        "slowdown",
        "fiscal_consolidation",
    }
    for reason in rejected.values():
        assert reason
    outlook = REGIME_ASSESSMENT["evidence"]["outlook_FORECAST_not_observation"]
    assert outlook  # forecasts are labelled, never stored as observations


def test_not_stored_indicators_are_absent_not_estimated():
    stored_codes = {o["indicator_code"] for o in OBSERVATIONS}
    assert "cpi_yoy_oct2026" not in stored_codes
    for key, unblocker in NOT_STORED.items():
        assert unblocker  # every gap names its exact unblocker
    assert len(NOT_STORED) == 8
