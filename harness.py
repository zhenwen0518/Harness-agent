import sys
import json
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path

from store import new_session, load_queue, save_queue, log_event, get_pending_tasks, update_task, expand_task
from worker import run_worker
from brain import decompose_goal, is_complex, decompose_task

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
                        print(f"[Task {task['id']}] 任务较复杂，正在拆分...")
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
                    else:
                        print(f"[Task {task['id']}] 开始：{task['description'][:60]}...")
                        update_task(queue, task["id"], status="RUNNING",
                                    started_at=datetime.now().isoformat())
                        log_event(session_id, {"type": "task_start", "task_id": task["id"]})
                        futures[task["id"]] = executor.submit(run_worker, task["description"], worker_cmd)

            done_ids = []
            for task_id, future in list(futures.items()):
                if future.done():
                    success, output = future.result()
                    if success:
                        print(f"[Task {task_id}] ✓ 完成")
                        update_task(queue, task_id, status="DONE", result=output,
                                    finished_at=datetime.now().isoformat())
                        log_event(session_id, {"type": "task_done", "task_id": task_id,
                                               "result": output[:500]})
                    else:
                        print(f"[Task {task_id}] ✗ 失败: {output[:100]}")
                        update_task(queue, task_id, status="FAILED", result=output,
                                    finished_at=datetime.now().isoformat())
                        log_event(session_id, {"type": "task_failed", "task_id": task_id,
                                               "error": output})
                        _cascade_fail(queue, task_id, session_id)
                    done_ids.append(task_id)

            for task_id in done_ids:
                del futures[task_id]

            all_statuses = {t["status"] for t in queue["tasks"]}
            if not futures and all_statuses <= {"DONE", "FAILED"}:
                break

            if not futures and not get_pending_tasks(queue):
                print("[Harness] 警告：存在无法解决的任务依赖，终止执行")
                break

            time.sleep(0.5)

    failed = any(t["status"] == "FAILED" for t in queue["tasks"])
    queue["status"] = "FAILED" if failed else "DONE"
    save_queue(queue)
    log_event(session_id, {"type": "session_done", "status": queue["status"]})
    if failed:
        print("\n[Harness] 执行完成，部分任务失败。事件记录于 session_store.jsonl")
    else:
        print("\n[Harness] 全部完成。事件记录于 session_store.jsonl")


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
