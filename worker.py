import subprocess


def run_worker(task_description: str, worker_command: list[str] | None = None) -> tuple[bool, str]:
    if worker_command is None:
        worker_command = ["claude", "-p"]

    result = subprocess.run(
        worker_command + [task_description],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode == 0:
        return True, result.stdout.strip()
    else:
        return False, result.stderr.strip()
