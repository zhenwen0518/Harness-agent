import json
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def clean_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_new_session_structure():
    from store import new_session
    q = new_session("build a todo app")
    assert q["goal"] == "build a todo app"
    assert q["status"] == "PENDING"
    assert q["tasks"] == []
    assert len(q["session_id"]) == 8


def test_save_and_load_queue(tmp_path):
    from store import new_session, save_queue, load_queue
    q = new_session("test goal")
    save_queue(q)
    loaded = load_queue()
    assert loaded["goal"] == "test goal"


def test_load_queue_returns_none_when_missing():
    from store import load_queue
    result = load_queue()
    assert result is None


def test_get_pending_tasks_no_deps():
    from store import new_session, get_pending_tasks
    q = new_session("goal")
    q["tasks"] = [
        {"id": "t1", "description": "task1", "status": "PENDING", "depends_on": [], "result": None, "started_at": None, "finished_at": None},
        {"id": "t2", "description": "task2", "status": "PENDING", "depends_on": [], "result": None, "started_at": None, "finished_at": None},
    ]
    pending = get_pending_tasks(q)
    assert len(pending) == 2


def test_get_pending_tasks_blocks_on_deps():
    from store import new_session, get_pending_tasks
    q = new_session("goal")
    q["tasks"] = [
        {"id": "t1", "description": "task1", "status": "PENDING", "depends_on": [], "result": None, "started_at": None, "finished_at": None},
        {"id": "t2", "description": "task2", "status": "PENDING", "depends_on": ["t1"], "result": None, "started_at": None, "finished_at": None},
    ]
    pending = get_pending_tasks(q)
    assert len(pending) == 1
    assert pending[0]["id"] == "t1"


def test_get_pending_tasks_unblocks_after_dep_done():
    from store import new_session, get_pending_tasks
    q = new_session("goal")
    q["tasks"] = [
        {"id": "t1", "description": "task1", "status": "DONE", "depends_on": [], "result": "ok", "started_at": None, "finished_at": None},
        {"id": "t2", "description": "task2", "status": "PENDING", "depends_on": ["t1"], "result": None, "started_at": None, "finished_at": None},
    ]
    pending = get_pending_tasks(q)
    assert len(pending) == 1
    assert pending[0]["id"] == "t2"


def test_update_task_status(tmp_path):
    from store import new_session, save_queue, update_task, load_queue
    q = new_session("goal")
    q["tasks"] = [
        {"id": "t1", "description": "task1", "status": "PENDING", "depends_on": [], "result": None, "started_at": None, "finished_at": None},
    ]
    save_queue(q)
    update_task(q, "t1", status="DONE", result="output")
    loaded = load_queue()
    assert loaded["tasks"][0]["status"] == "DONE"
    assert loaded["tasks"][0]["result"] == "output"


def test_log_event_appends(tmp_path):
    from store import log_event
    log_event("sess1", {"type": "task_start", "task_id": "t1"})
    log_event("sess1", {"type": "task_done", "task_id": "t1", "result": "ok"})
    lines = Path("session_store.jsonl").read_text().strip().split("\n")
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["type"] == "task_start"
    assert first["session_id"] == "sess1"
    assert "ts" in first
