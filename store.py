import json
import uuid
from datetime import datetime
from pathlib import Path

QUEUE_FILE = Path("task_queue.json")
SESSION_FILE = Path("session_store.jsonl")


def new_session(goal: str) -> dict:
    return {
        "session_id": str(uuid.uuid4())[:8],
        "goal": goal,
        "created_at": datetime.now().isoformat(),
        "status": "PENDING",
        "tasks": []
    }


def load_queue() -> dict | None:
    if not QUEUE_FILE.exists():
        return None
    return json.loads(QUEUE_FILE.read_text())


def save_queue(queue: dict):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False))


def log_event(session_id: str, event: dict):
    event["ts"] = datetime.now().isoformat()
    event["session_id"] = session_id
    with SESSION_FILE.open("a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def get_pending_tasks(queue: dict) -> list[dict]:
    done_ids = {t["id"] for t in queue["tasks"] if t["status"] == "DONE"}
    return [
        t for t in queue["tasks"]
        if t["status"] == "PENDING"
        and all(dep in done_ids for dep in t["depends_on"])
    ]


def update_task(queue: dict, task_id: str, **kwargs):
    for task in queue["tasks"]:
        if task["id"] == task_id:
            task.update(kwargs)
            break
    save_queue(queue)


def expand_task(queue: dict, task_id: str, subtasks: list[dict]):
    subtask_ids = {t["id"] for t in subtasks}
    depended_within = {dep for t in subtasks for dep in t["depends_on"] if dep in subtask_ids}
    terminal_ids = sorted(subtask_ids - depended_within)

    for task in queue["tasks"]:
        if task_id in task["depends_on"]:
            task["depends_on"] = [dep for dep in task["depends_on"] if dep != task_id]
            task["depends_on"].extend(terminal_ids)

    idx = next(i for i, t in enumerate(queue["tasks"]) if t["id"] == task_id)
    queue["tasks"] = queue["tasks"][:idx] + subtasks + queue["tasks"][idx + 1:]
    save_queue(queue)
