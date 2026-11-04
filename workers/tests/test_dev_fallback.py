"""Dev-fallback queue tests — stdlib SQLite only, no Redis (Phase 2, Team E)."""

import json

from workers import dev_fallback


def test_enqueue_run_status(tmp_path):
    path = str(tmp_path / "q.db")
    job_id = dev_fallback.enqueue("add", [2, 3], path=path)
    assert job_id == 1
    outcomes = dev_fallback.run_once(path=path)
    assert outcomes[0]["status"] == "done"
    assert outcomes[0]["result"] == 5
    rows = dev_fallback.status(path=path)
    assert rows[0]["status"] == "done"
    assert json.loads(rows[0]["result"]) == 5


def test_unknown_task_rejected(tmp_path):
    path = str(tmp_path / "q.db")
    try:
        dev_fallback.enqueue("nope", [], path=path)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unknown task was accepted")
