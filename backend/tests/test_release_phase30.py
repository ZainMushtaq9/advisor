"""Phase 30 release guards.

These tests guard the release artefacts themselves, not financial
computation: the handover report must carry the six-way separation and
the Phase 29 gate verbatim (no upgraded verdicts, no claimed sign-off),
the changelog must carry the handover entry, and the README must carry
the Phase 30 status section. Content checks are substring checks on
stable strings the Phase 30 docs deliberately contain.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relpath):
    path = REPO_ROOT / relpath
    assert path.exists(), f"missing release artefact: {relpath}"
    return path.read_text(encoding="utf-8")


def test_handover_report_has_six_way_separation():
    text = _read("docs/phase-30/handover_report.md")
    for section in (
        "IMPLEMENTED",
        "VERIFIED",
        "PARTIALLY VERIFIED",
        "UNAVAILABLE",
        "BLOCKED",
        "PLANNED",
    ):
        assert section in text, f"handover report missing section: {section}"


def test_handover_report_carries_phase29_gate_verbatim():
    text = _read("docs/phase-30/handover_report.md")
    # G1 NOT_MET (HBL chain blocked) and G5 PARTIAL (human sign-off
    # pending) must appear exactly as judged in Phase 29; no upgrade.
    assert "G1 NOT_MET" in text
    assert "G5 PARTIAL" in text
    assert "no human sign-off is claimed" in text


def test_handover_report_states_system_verdict():
    text = _read("docs/phase-30/handover_report.md")
    assert "PARTIALLY COMPLETE" in text
    assert "HBL" in text


def test_changelog_has_handover_entry():
    text = _read("CHANGELOG.md")
    assert "[0.2.0-handover]" in text


def test_readme_has_phase30_status_section():
    text = _read("README.md")
    assert "Phase 30 handover" in text
    assert "NOT a production release" in text
