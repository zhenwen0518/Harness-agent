from unittest.mock import patch, MagicMock


def test_run_worker_success():
    from worker import run_worker
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "task completed successfully"
    mock_result.stderr = ""

    with patch("worker.subprocess.run", return_value=mock_result) as mock_run:
        success, output = run_worker("write a hello world function", ["claude", "-p"])

    assert success is True
    assert output == "task completed successfully"
    mock_run.assert_called_once_with(
        ["claude", "-p", "write a hello world function"],
        capture_output=True, text=True, timeout=300
    )


def test_run_worker_failure():
    from worker import run_worker
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error: command not found"

    with patch("worker.subprocess.run", return_value=mock_result):
        success, output = run_worker("some task", ["claude", "-p"])

    assert success is False
    assert "error" in output


def test_run_worker_default_command():
    from worker import run_worker
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "done"
    mock_result.stderr = ""

    with patch("worker.subprocess.run", return_value=mock_result) as mock_run:
        run_worker("task description")

    args = mock_run.call_args[0][0]
    assert args[0] == "claude"
    assert args[1] == "-p"
    assert args[2] == "task description"
