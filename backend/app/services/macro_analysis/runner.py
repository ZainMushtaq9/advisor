"""Phase 10 runner: seed macro observations, exposures, sector profiles,
regimes and events idempotently.

Reads ONLY the registries in app.services.macro_analysis (values collected
from SBP/PBS pages read directly in this run, plus press-sourced events
with press source keys). Writes nothing in dry-run mode; --commit writes
idempotently — a second --commit writes 0 new rows (skipped_existing).

Every written row is UNVERIFIED unless the registry assigns a higher
status with a documented second-source basis (rule H1); calculation
never upgrades a status. No row is ever edited: revisions are new
versions, and the versioned/immutable triggers enforce that.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models.analysis import EconomicIndicator, SectorMetricProfile
from app.models.governance import DataSource
from app.models.macro import CompanyMacroExposure, MacroEvent, MacroRegime
from app.models.reference import Security
from app.services.macro_analysis import (
    EVENTS,
    EXPOSURES,
    INDICATORS,
    OBSERVATIONS,
    REGIME_ASSESSMENT,
    SECTOR_PROFILES,
)

PKT = ZoneInfo("Asia/Karachi")

SOURCES = {
    "sbp_mps_oct_2026": (
        "SBP Monetary Policy Statement, 26 October 2026",
        "official_central_bank",
        "https://www.sbp.org.pk/assets/document/publications/MPS-Oct-2026-Eng.pdf",
        "Official SBP publication, read directly. Internal analysis only; no republication.",
    ),
    "pbs_homepage": (
        "Pakistan Bureau of Statistics homepage headline values",
        "official_statistics",
        "https://www.pbs.gov.pk/page/8/",
        "Official PBS page, read directly. Headline values only; publication dates not shown on the"
        " page, so source_timestamp is NULL and point-in-time falls back to collected_at.",
    ),
    "press_brecorder_pbs_release": (
        "Business Recorder reporting the PBS October 2026 CPI release",
        "press_reporting",
        "https://www.brecorder.com/news/40447159/oct-cpi-rises-96pc-yoy",
        "Press reporting of an official release, NOT the official release itself. Never keyed as an"
        " official source.",
    ),
    "press_pakera_mps_minutes": (
        "Pakera reporting the SBP MPC minutes due date",
        "press_reporting",
        "https://pakera.pk/sbp-next-monetary-policy-meeting-14-december-2026/",
        "Single press source. Confirm against sbp.org.pk before relying on it.",
    ),
    "press_pakera_sbp_calendar": (
        "Pakera reading the SBP FY27 MPC advance calendar",
        "press_reporting",
        "https://pakera.pk/sbp-next-monetary-policy-meeting-14-december-2026/",
        "Press reading of the SBP calendar, corroborated by a second press source; the SBP calendar"
        " page itself was not directly read.",
    ),
}


def _parse_date(d: str | None) -> date | None:
    return date.fromisoformat(d) if d else None


def _as_pktop_midnight(d: str | None) -> datetime | None:
    if not d:
        return None
    return datetime.combine(date.fromisoformat(d), datetime.min.time(), tzinfo=PKT)


def get_or_create_source(session: Session, source_key: str) -> DataSource:
    display_name, source_type, base_reference, terms_summary = SOURCES[source_key]
    row = session.query(DataSource).filter_by(source_key=source_key).one_or_none()
    if row is None:
        row = DataSource(
            source_key=source_key,
            display_name=display_name,
            source_type=source_type,
            base_reference=base_reference,
            verification_status="UNVERIFIED",
            terms_summary=terms_summary,
        )
        session.add(row)
        session.flush()
    return row


def run_macro(session: Session, commit: bool) -> dict:
    """Seed everything Phase 10 v1 holds. Returns a counts report."""
    report: dict = {
        "observations_written": 0,
        "observations_skipped_existing": 0,
        "exposures_written": 0,
        "exposures_skipped_existing": 0,
        "profiles_written": 0,
        "profiles_skipped_existing": 0,
        "regimes_written": 0,
        "regimes_skipped_existing": 0,
        "events_written": 0,
        "events_skipped_existing": 0,
        "sources_written": 0,
        "sources_skipped_existing": 0,
        "indicators_registered": len(INDICATORS),
        "verified_observations": 0,
        "unverified_observations": 0,
        "pending_companies": ["HBL"],
        "not_stored": [
            "cpi_yoy_oct2026",
            "kibor_yields",
            "usd_pkr_rate",
            "oil_commodity_prices",
            "remittances_level",
            "trade_figures",
            "fiscal_balances",
            "budget_events",
        ],
    }
    now = datetime.now(PKT)
    sources: dict[str, DataSource] = {}
    for key in SOURCES:
        existing = session.query(DataSource).filter_by(source_key=key).one_or_none()
        if existing is not None:
            sources[key] = existing
            report["sources_skipped_existing"] += 1
        else:
            sources[key] = get_or_create_source(session, key)
            report["sources_written"] += 1

    for obs in OBSERVATIONS:
        obs_date = _parse_date(obs["observation_date"])
        existing = (
            session.query(EconomicIndicator)
            .filter_by(
                indicator_code=obs["indicator_code"],
                observation_date=obs_date,
                version_number=1,
            )
            .one_or_none()
        )
        if existing is not None:
            report["observations_skipped_existing"] += 1
            continue
        if obs["quality_status"] == "VERIFIED":
            report["verified_observations"] += 1
        else:
            report["unverified_observations"] += 1
        if commit:
            session.add(
                EconomicIndicator(
                    indicator_code=obs["indicator_code"],
                    indicator_name=INDICATORS[obs["indicator_code"]]["name"],
                    observation_date=obs_date,
                    value=Decimal(obs["value"]),
                    unit=INDICATORS[obs["indicator_code"]]["unit"],
                    frequency=INDICATORS[obs["indicator_code"]]["frequency"],
                    data_source_id=sources[obs["source_key"]].id,
                    source_key=obs["source_key"],
                    source_timestamp=_as_pktop_midnight(obs["source_timestamp"]),
                    collected_at=now,
                    quality_status=obs["quality_status"],
                    version_number=1,
                    supersedes_id=None,
                    is_current=True,
                )
            )
        report["observations_written"] += 1

    for exp in EXPOSURES:
        # Exposures are seeded by ticker; the live company id is resolved
        # from the database (surrogate ids shift across registry imports).
        exp_company = (
            session.query(Security).filter(Security.ticker == exp["ticker"]).first()
        )
        if exp_company is None:
            report["exposures_skipped_existing"] += 1
            continue
        exp_company_id = exp_company.company_id
        existing = (
            session.query(CompanyMacroExposure)
            .filter_by(
                company_id=exp_company_id,
                exposure_key=exp["exposure_key"],
                is_current=True,
            )
            .one_or_none()
        )
        if existing is not None:
            report["exposures_skipped_existing"] += 1
            continue
        if commit:
            session.add(
                CompanyMacroExposure(
                    company_id=exp_company_id,
                    exposure_key=exp["exposure_key"],
                    exposure_name=exp["exposure_name"],
                    direction=exp["direction"],
                    evidence_type=exp["evidence_type"],
                    evidence_ref=exp["evidence_ref"],
                    note=exp["note"],
                    data_source_id=None,
                    source_key="phase07_statements",
                    source_timestamp=None,
                    collected_at=now,
                    quality_status=exp["quality_status"],
                    version_number=1,
                    supersedes_id=None,
                    is_current=True,
                )
            )
        report["exposures_written"] += 1

    for prof in SECTOR_PROFILES:
        existing = (
            session.query(SectorMetricProfile)
            .filter_by(
                sector_id=prof["sector_id"],
                metric_key=prof["metric_key"],
            )
            .one_or_none()
        )
        if existing is not None:
            report["profiles_skipped_existing"] += 1
            continue
        if commit:
            session.add(
                SectorMetricProfile(
                    sector_id=prof["sector_id"],
                    metric_key=prof["metric_key"],
                    applicability=prof["applicability"],
                    source_requirements=prof["source_requirements"],
                    is_active=True,
                )
            )
        report["profiles_written"] += 1

    regime = REGIME_ASSESSMENT
    regime_date = _parse_date(regime["observation_date"])
    existing_regime = (
        session.query(MacroRegime)
        .filter_by(
            observation_date=regime_date,
            regime_label=regime["regime_label"],
            method_version=regime["method_version"],
        )
        .one_or_none()
    )
    if existing_regime is not None:
        report["regimes_skipped_existing"] += 1
    else:
        if commit:
            session.add(
                MacroRegime(
                    observation_date=regime_date,
                    regime_label=regime["regime_label"],
                    method_version=regime["method_version"],
                    evidence=regime["evidence"],
                    data_source_id=sources[regime["source_key"]].id,
                    source_key=regime["source_key"],
                    source_timestamp=_as_pktop_midnight(regime["source_timestamp"]),
                    collected_at=now,
                    quality_status=regime["quality_status"],
                )
            )
        report["regimes_written"] += 1

    for ev in EVENTS:
        existing = (
            session.query(MacroEvent)
            .filter_by(
                event_date=_parse_date(ev["event_date"]),
                event_type=ev["event_type"],
                title=ev["title"],
            )
            .one_or_none()
        )
        if existing is not None:
            report["events_skipped_existing"] += 1
            continue
        if commit:
            session.add(
                MacroEvent(
                    event_date=_parse_date(ev["event_date"]),
                    event_type=ev["event_type"],
                    title=ev["title"],
                    note=ev["note"],
                    data_source_id=sources[ev["source_key"]].id,
                    source_key=ev["source_key"],
                    source_timestamp=_as_pktop_midnight(ev["source_timestamp"]),
                    collected_at=now,
                    quality_status=ev["quality_status"],
                )
            )
        report["events_written"] += 1

    if commit:
        session.commit()
    else:
        session.rollback()
    return report
