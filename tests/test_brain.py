import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def clean_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_decompose_goal_stub_mode_no_config():
    from brain import decompose_goal
    tasks = decompose_goal("build a todo app")
    assert len(tasks) == 1
    assert tasks[0]["id"] == "t1"
    assert tasks[0]["description"] == "build a todo app"
    assert tasks[0]["depends_on"] == []


def test_decompose_goal_stub_mode_explicit(tmp_path):
    from brain import decompose_goal
    (tmp_path / "config.json").write_text(json.dumps({
        "brain_provider": "stub"
    }))
    tasks = decompose_goal("write a script")
    assert tasks[0]["description"] == "write a script"


def test_decompose_goal_api_mode_parses_json(tmp_path):
    from brain import decompose_goal
    (tmp_path / "config.json").write_text(json.dumps({
        "brain_provider": "openai_compatible",
        "brain_api_key": "sk-test",
        "brain_model": "deepseek-chat",
        "brain_base_url": "https://api.deepseek.com/v1"
    }))

    fake_tasks = [
        {"id": "t1", "description": "design database schema", "depends_on": []},
        {"id": "t2", "description": "implement backend API", "depends_on": ["t1"]}
    ]
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": json.dumps(fake_tasks)}}]
    }

    with patch("brain.requests.post", return_value=fake_response):
        tasks = decompose_goal("build a todo app")

    assert len(tasks) == 2
    assert tasks[1]["depends_on"] == ["t1"]


def test_decompose_goal_api_mode_handles_markdown_json(tmp_path):
    from brain import decompose_goal
    (tmp_path / "config.json").write_text(json.dumps({
        "brain_provider": "openai_compatible",
        "brain_api_key": "sk-test",
        "brain_model": "deepseek-chat",
        "brain_base_url": "https://api.deepseek.com/v1"
    }))

    wrapped_in_markdown = '```json\n[{"id": "t1", "description": "task", "depends_on": []}]\n```'
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": wrapped_in_markdown}}]
    }

    with patch("brain.requests.post", return_value=fake_response):
        tasks = decompose_goal("goal")

    assert tasks[0]["id"] == "t1"
