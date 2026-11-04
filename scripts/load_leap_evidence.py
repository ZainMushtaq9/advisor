"""Load SECP LEAP browser observations into registry_evidence.

Implements docs/phase-04/field_scoped_leap_promotion_procedure.md.
Input: a JSON file produced by the live-browser run described in
docs/phase-04/sampled_verification_plan_2026-11-04.md.

    {
      "collected_date": "2026-11-04",
      "observations": [
        {
          "company_id": 289,
          "ticker": "HUBC",
          "registry_legal_name": "The Hub Power Company Limited",
          "query_wordings": ["The Hub Power Company Limited", "Hub Power"],
          "query_that_found": "Hub Power",
          "incorporated_row": {"name": "...", "cuin": "0024725",
            "incorporation_date": "01-08-1991", "cro_city": "Karachi"},
          "organization_row": {"name": "...", "displayed_date": "08-01-3991"},
          "other_candidates": ["HUB POWER HOLDINGS LIMITED"],
          "outcome": "AGREE",
          "notes": ""
        }
      ]
    }

Fail-fast rules (exit 2, nothing written):
- any observation fails pure validation (see leap_evidence module);
- company_id unknown, or its ticker / legal_name differs from the
  JSON (the registry must not have moved under the sample);
- an existing secp_leap row for the company conflicts with the new
  row (identical existing rows are skipped, never duplicated).

This script NEVER calls apply_verification_rules, NEVER changes
companies.status / securities.status, and NEVER writes
company_identifiers. --dry-run is the default; --commit writes.

Usage:
    DATABASE_URL=... python3 scripts/load_leap_evidence.py \
        --input docs/phase-04/leap_observations.json [--commit]

DATABASE_URL is read from the environment only and is never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models.governance import DataSource  # noqa: E402
from app.models.reference import Company, Security  # noqa: E402
from app.models.registry import RegistryEvidence  # noqa: E402
from app.services.registry.leap_evidence import (  # noqa: E402
    SOURCE_KEY,
    observation_to_evidence_row,
    validate_observation,
)

DATA_SOURCE_ROW = {
    "source_key": SOURCE_KEY,
    "display_name": "SECP LEAP public company-name search",
    "source_type": "regulator_search",
    "base_reference": "https://leap.secp.gov.pk/#/landing-page",
    "verification_status": "UNVERIFIED",
    "terms_summary": (
        "Public company-name search; no sign-in, fee, or CAPTCHA on "
        "the search box. Sampled manual use only; bulk scraping not "
        "approved. Page disclaimer: system-generated information, no "
        "name-reservation right, Registrar decides."
    ),
    "reliability_notes": (
        "Returns name, CUIN, incorporation date, CRO city, status "
        "badge only. No sector, no ticker. Every company appears "
        "twice (organization row with garbled year + INCORPORATED "
        "row); the INCORPORATED row is the observation."
    ),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="observations JSON file")
    parser.add_argument("--commit", action="store_true",
                        help="write rows (default is --dry-run)")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        fail("DATABASE_URL must be set")

    with open(args.input, encoding="utf-8") as handle:
        payload = json.load(handle)
    observations = payload.get("observations")
    if not isinstance(observations, list) or not observations:
        fail("input must contain a non-empty 'observations' list")

    engine = create_engine(database_url)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        rows: list[dict] = []
        for obs in observations:
            company = session.query(Company).filter_by(
                id=obs.get("company_id")).first()
            if company is None:
                fail(f"unknown company_id {obs.get('company_id')!r}")
            security = session.query(Security).filter_by(
                company_id=company.id).first()
            if security is None or security.ticker != obs.get("ticker"):
                fail(
                    f"ticker mismatch for company_id {company.id}: "
                    f"DB has {security.ticker if security else None!r}, "
                    f"JSON has {obs.get('ticker')!r}"
                )
            if company.legal_name != obs.get("registry_legal_name"):
                fail(
                    f"legal_name mismatch for company_id {company.id}: "
                    f"DB has {company.legal_name!r}, JSON has "
                    f"{obs.get('registry_legal_name')!r}"
                )
            errors = validate_observation(obs, company.legal_name)
            if errors:
                fail(f"company_id {company.id} invalid: " + "; ".join(errors))
            rows.append(observation_to_evidence_row(obs))

        existing = {
            (r.entity_id, r.source_record_key): r
            for r in session.query(RegistryEvidence)
            .filter_by(source_key=SOURCE_KEY).all()
        }
        to_insert: list[dict] = []
        skipped = 0
        for row in rows:
            key = (row["entity_id"], row["source_record_key"])
            if key in existing:
                old = existing[key]
                if (old.observed_name == row["observed_name"]
                        and old.evidence_note == row["evidence_note"]):
                    skipped += 1
                    continue
                fail(
                    f"conflicting existing secp_leap row for company_id "
                    f"{row['entity_id']} (source_record_key "
                    f"{row['source_record_key']!r}); refusing to overwrite"
                )
            to_insert.append(row)

        print(f"observations validated: {len(rows)}")
        print(f"would insert: {len(to_insert)}, would skip (identical): {skipped}")
        for row in to_insert:
            print(f"  company_id={row['entity_id']} "
                  f"key={row['source_record_key']} "
                  f"observed_name={row['observed_name']!r}")
        if not args.commit:
            print("dry-run only: nothing written (pass --commit to write)")
            return

        data_source = session.query(DataSource).filter_by(
            source_key=SOURCE_KEY).first()
        if data_source is None:
            session.add(DataSource(**DATA_SOURCE_ROW))
            print("data_sources: inserted secp_leap provenance row")
        for row in rows:
            if (row["entity_id"], row["source_record_key"]) in existing:
                continue
            collected = payload.get("collected_date")
            collected_at = None
            if collected:
                collected_at = datetime.strptime(
                    collected, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            session.add(RegistryEvidence(
                collected_at=collected_at, **row))
        session.commit()
        print(f"committed: {len(to_insert)} evidence rows")
        print("statuses unchanged by design (see procedure §6)")
    finally:
        session.close()


if __name__ == "__main__":
    main()
