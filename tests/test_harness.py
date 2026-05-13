import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def clean_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_main_no_args_exits(capsys):
    import sys
    with patch.object(sys, "argv", ["harness.py"]):
        with pytest.raises(SystemExit) as exc:
            from harness import main
            main()
    assert exc.value.code == 1


def test_resume_no_queue_exits(capsys):
    import sys
    with patch.object(sys, "argv", ["harness.py", "--resume"]):
        with pytest.raises(SystemExit) as exc:
            from harness import main
            main()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "没有找到" in captured.out


def test_resume_resets_running_tasks(tmp_path):
    from store import new_session, save_queue
    q = new_session("goal")
    q["tasks"] = [
        {"id": "t1", "description": "task1", "status": "RUNNING",
         "depends_on": [], "result": None, "started_at": None, "finished_at": None},
    ]
    save_queue(q)

    import sys
    with patch.object(sys, "argv", ["harness.py", "--resume"]):
        with patch("harness.execute_queue") as mock_exec:
            from harness import main
            main()

    call_args = mock_exec.call_args[0][0]
    assert call_args["tasks"][0]["status"] == "PENDING"


def test_confirm_tasks_yes(monkeypatch):
    from harness import confirm_tasks
    monkeypatch.setattr("builtins.input", lambda _: "y")
    tasks = [{"id": "t1", "description": "task", "depends_on": []}]
    assert confirm_tasks(tasks) is True


def test_confirm_tasks_no(monkeypatch):
    from harness import confirm_tasks
    monkeypatch.setattr("builtins.input", lambda _: "n")
    tasks = [{"id": "t1", "description": "task", "depends_on": []}]
    assert confirm_tasks(tasks) is False
