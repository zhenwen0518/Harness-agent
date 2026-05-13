import os
import sys
import json
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path

from store import new_session, load_queue, save_queue, log_event, get_pending_tasks, update_task, expand_task
from worker import run_worker
from brain import decompose_goal, is_complex, decompose_task

_STATUS_ICON  = {"PENDING": "○", "RUNNING": "◉", "DONE": "✓", "FAILED": "✗"}
_STATUS_COLOR = {"PENDING": "\033[90m", "RUNNING": "\033[34m", "DONE": "\033[32m", "FAILED": "\033[31m"}
_RESET = "\033[0m"
_BOLD  = "\033[1m"


def _render(queue: dict):
    tasks   = queue["tasks"]
    total   = len(tasks)
    done    = sum(1 for t in tasks if t["status"] == "DONE")
    failed  = sum(1 for t in tasks if t["status"] == "FAILED")
    running = sum(1 for t in tasks if t["status"] == "RUNNING")

    lines = [
        f"{_BOLD}目标：{_RESET}{queue['goal']}",
        f"进度：{done}/{total} 完成  {running} 运行中  {failed} 失败",
        "",
        f"{'ID':<10} {'状态':<8} {'耗时':<6} 描述",
        "─" * 72,
    ]
    for t in tasks:
        icon  = _STATUS_ICON.get(t["status"], "?")
        color = _STATUS_COLOR.get(t["status"], "")
        start = datetime.fromisoformat(t["started_at"]) if t.get("started_at") else None
        end   = datetime.fromisoformat(t["finished_at"]) if t.get("finished_at") else None
        dur   = f"{int(((end or datetime.now()) - start).total_seconds())}s" if start else "-"
        desc  = t["description"][:54] + ("…" if len(t["description"]) > 54 else "")
        lines.append(f"{t['id']:<10} {color}{icon} {t['status']:<7}{_RESET} {dur:<6} {desc}")
        if t["status"] == "FAILED" and t.get("result"):
            lines.append(f"{'':10}   {_STATUS_COLOR['FAILED']}↳ {t['result'][:80].replace(chr(10),' ')}{_RESET}")
    return "\n".join(lines)


def _refresh(queue: dict):
    os.system("clear")
    print(_render(queue))
    print()

MAX_DEPTH = 2


def _load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text())


def confirm_tasks(tasks: list[dict]) -> bool:
    print("\n[Harness] 拆解出以下任务，请确认：\n")
    for task in tasks:
        deps = f"  (依赖: {', '.join(task['depends_on'])})" if task["depends_on"] else ""
        print(f"  {task['id']}. {task['description']}{deps}")
    print()
    answer = input("确认执行？(y/n): ").strip().lower()
    return answer == "y"


def _cascade_fail(queue: dict, failed_id: str, session_id: str):
    failed_ids = {failed_id}
    changed = True
    while changed:
        changed = False
        for task in queue["tasks"]:
            if task["status"] == "PENDING" and set(task["depends_on"]) & failed_ids:
                task["status"] = "FAILED"
                task["result"] = f"依赖任务 {set(task['depends_on']) & failed_ids} 失败，跳过执行"
                log_event(session_id, {"type": "task_failed", "task_id": task["id"],
                                       "error": task["result"]})
                failed_ids.add(task["id"])
                changed = True


def execute_queue(queue: dict, config: dict | None = None):
    if config is None:
        config = _load_config()

    session_id = queue["session_id"]
    max_workers = config.get("max_parallel_workers", 3)
    worker_cmd = config.get("worker_command", ["claude", "-p"])

    log_event(session_id, {"type": "session_start", "goal": queue["goal"]})
    queue["status"] = "RUNNING"
    save_queue(queue)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        while True:
            pending = get_pending_tasks(queue)

            for task in pending:
                if task["id"] not in futures:
                    depth = task.get("depth", 0)
                    if depth < MAX_DEPTH and is_complex(task["description"]):
                        subtasks = decompose_task(task["description"], task["id"])
                        for st in subtasks:
                            st.setdefault("status", "PENDING")
                            st.setdefault("result", None)
                            st.setdefault("started_at", None)
                            st.setdefault("finished_at", None)
                            st["depth"] = depth + 1
                        expand_task(queue, task["id"], subtasks)
                        log_event(session_id, {"type": "task_expanded", "task_id": task["id"],
                                               "subtasks": [s["id"] for s in subtasks]})
                        _refresh(queue)
                    else:
                        update_task(queue, task["id"], status="RUNNING",
                                    started_at=datetime.now().isoformat())
                        log_event(session_id, {"type": "task_start", "task_id": task["id"]})
                        futures[task["id"]] = executor.submit(run_worker, task["description"], worker_cmd)
                        _refresh(queue)

            done_ids = []
            for task_id, future in list(futures.items()):
                if future.done():
                    success, output = future.result()
                    if success:
                        update_task(queue, task_id, status="DONE", result=output,
                                    finished_at=datetime.now().isoformat())
                        log_event(session_id, {"type": "task_done", "task_id": task_id,
                                               "result": output[:500]})
                    else:
                        update_task(queue, task_id, status="FAILED", result=output,
                                    finished_at=datetime.now().isoformat())
                        log_event(session_id, {"type": "task_failed", "task_id": task_id,
                                               "error": output})
                        _cascade_fail(queue, task_id, session_id)
                    _refresh(queue)
                    done_ids.append(task_id)

            for task_id in done_ids:
                del futures[task_id]

            all_statuses = {t["status"] for t in queue["tasks"]}
            if not futures and all_statuses <= {"DONE", "FAILED"}:
                break

            if not futures and not get_pending_tasks(queue):
                _refresh(queue)
                print("[Harness] 警告：存在无法解决的任务依赖，终止执行")
                break

            time.sleep(0.5)

    failed = any(t["status"] == "FAILED" for t in queue["tasks"])
    queue["status"] = "FAILED" if failed else "DONE"
    save_queue(queue)
    log_event(session_id, {"type": "session_done", "status": queue["status"]})
    _refresh(queue)
    if failed:
        print("[Harness] 执行完成，部分任务失败。详情：python3 monitor.py --summary")
    else:
        print("[Harness] 全部完成。详情：python3 monitor.py --summary")


def main():
    config = _load_config()

    if "--resume" in sys.argv:
        queue = load_queue()
        if not queue:
            print("[Harness] 没有找到可续接的任务。")
            sys.exit(1)
        print(f"[Harness] 续接任务：{queue['goal']}")
        for task in queue["tasks"]:
            if task["status"] in ("RUNNING", "FAILED"):
                task["status"] = "PENDING"
        save_queue(queue)
        execute_queue(queue, config)
        return

    if len(sys.argv) < 2:
        print("用法: python harness.py \"你的目标\"  或  python harness.py --resume")
        sys.exit(1)

    goal = sys.argv[1]
    print(f"\n[Harness] 收到目标：{goal}")
    print("[Harness] 正在分析目标...")

    tasks = decompose_goal(goal)
    for task in tasks:
        task.setdefault("status", "PENDING")
        task.setdefault("result", None)
        task.setdefault("started_at", None)
        task.setdefault("finished_at", None)
        task.setdefault("depth", 0)
    queue = new_session(goal)
    queue["tasks"] = tasks

    if not confirm_tasks(tasks):
        print("[Harness] 已取消。")
        sys.exit(0)

    save_queue(queue)
    execute_queue(queue, config)


if __name__ == "__main__":
    main()
