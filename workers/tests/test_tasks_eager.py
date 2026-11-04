"""Worker probe-task tests — eager mode, no Redis needed (Phase 2, Team E).

Eager mode executes tasks in-process, so these tests prove task logic
and logging wiring, NOT the broker path. The broker path is proved by
the live run recorded in docs/phase-02/REDIS_SETUP.md.
"""

from workers.celery_app import app
from workers.tasks import add, health_probe

app.conf.task_always_eager = True
app.conf.task_store_eager_result = True


def test_add():
    result = add.delay(2, 3)
    assert result.get() == 5


def test_health_probe_shape():
    result = health_probe.delay().get()
    assert result["status"] == "ok"
    assert "timestamp_utc" in result
