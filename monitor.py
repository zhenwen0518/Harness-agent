"""
用法：
  python3 monitor.py           # 查看当前任务状态快照
  python3 monitor.py --watch   # 实时刷新（每秒更新）
  python3 monitor.py --tail    # 滚动显示事件日志
  python3 monitor.py --summary # 生成执行摘要报告
"""

import json
import sys
import time
import os
from datetime import datetime
from pathlib import Path

QUEUE_FILE = Path("task_queue.json")
SESSION_FILE = Path("session_store.jsonl")

STATUS_ICON = {
    "PENDING": "○",
    "RUNNING": "◉",
    "DONE":    "✓",
    "FAILED":  "✗",
}

STATUS_COLOR = {
    "PENDING": "\033[90m",   # 灰
    "RUNNING": "\033[34m",   # 蓝
    "DONE":    "\033[32m",   # 绿
    "FAILED":  "\033[31m",   # 红
}
RESET = "\033[0m"
BOLD  = "\033[1m"


def _color(status: str, text: str) -> str:
    return f"{STATUS_COLOR.get(status, '')}{text}{RESET}"


def _load_queue() -> dict | None:
    if not QUEUE_FILE.exists():
        return None
    try:
        return json.loads(QUEUE_FILE.read_text())
    except json.JSONDecodeError:
        return None


def _load_events() -> list[dict]:
    if not SESSION_FILE.exists():
        return []
    events = []
    for line in SESSION_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def _fmt_time(iso: str | None) -> str:
    if not iso:
        return "-"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return iso


def _duration(start: str | None, end: str | None) -> str:
    if not start:
        return "-"
    try:
        s = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end) if end else datetime.now()
        secs = int((e - s).total_seconds())
        return f"{secs}s"
    except ValueError:
        return "-"


def _render_status(queue: dict) -> str:
    lines = []
    lines.append(f"{BOLD}目标：{RESET}{queue['goal']}")
    lines.append(f"会话：{queue['session_id']}  创建：{_fmt_time(queue.get('created_at'))}  "
                 f"状态：{_color(queue['status'], queue['status'])}")
    lines.append("")

    tasks = queue.get("tasks", [])
    total  = len(tasks)
    done   = sum(1 for t in tasks if t["status"] == "DONE")
    failed = sum(1 for t in tasks if t["status"] == "FAILED")
    running= sum(1 for t in tasks if t["status"] == "RUNNING")

    lines.append(f"进度：{done}/{total} 完成  {running} 运行中  {failed} 失败")
    lines.append("")
    lines.append(f"{'ID':<10} {'状态':<10} {'开始':<10} {'耗时':<8} 描述")
    lines.append("-" * 80)

    for t in tasks:
        icon = STATUS_ICON.get(t["status"], "?")
        status_str = _color(t["status"], f"{icon} {t['status']:<8}")
        start = _fmt_time(t.get("started_at"))
        dur   = _duration(t.get("started_at"), t.get("finished_at"))
        desc  = t["description"][:52] + ("…" if len(t["description"]) > 52 else "")
        lines.append(f"{t['id']:<10} {status_str} {start:<10} {dur:<8} {desc}")

        if t["status"] == "FAILED" and t.get("result"):
            err = t["result"][:100].replace("\n", " ")
            lines.append(f"{'':10}   {_color('FAILED', '↳ ' + err)}")

    return "\n".join(lines)


def cmd_snapshot():
    queue = _load_queue()
    if not queue:
        print("未找到 task_queue.json，请先运行 harness.py 启动任务。")
        return
    print(_render_status(queue))


def cmd_watch():
    print("实时监控中（Ctrl+C 退出）…\n")
    try:
        while True:
            queue = _load_queue()
            os.system("clear")
            if not queue:
                print("等待任务启动…")
            else:
                print(_render_status(queue))
                if queue["status"] in ("DONE", "FAILED"):
                    print(f"\n任务已结束（{queue['status']}），监控停止。")
                    break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n已退出监控。")


def cmd_tail(n: int = 30):
    events = _load_events()
    if not events:
        print("暂无事件记录。")
        return

    recent = events[-n:]
    print(f"{BOLD}最近 {len(recent)} 条事件：{RESET}\n")
    for e in recent:
        ts   = _fmt_time(e.get("ts"))
        etype = e.get("type", "unknown")
        tid  = e.get("task_id", "")

        if etype == "task_done":
            label = _color("DONE", "✓ DONE")
        elif etype == "task_failed":
            label = _color("FAILED", "✗ FAILED")
        elif etype == "task_start":
            label = _color("RUNNING", "◉ START")
        elif etype == "task_expanded":
            label = "\033[33m⊕ EXPAND\033[0m"
        elif etype == "session_start":
            label = f"{BOLD}▶ SESSION_START{RESET}"
        elif etype == "session_done":
            label = f"{BOLD}■ SESSION_DONE{RESET}"
        else:
            label = etype

        detail = ""
        if etype == "task_failed" and e.get("error"):
            detail = "  " + e["error"][:80].replace("\n", " ")
        if etype == "task_expanded":
            detail = "  子任务: " + ", ".join(e.get("subtasks", []))

        print(f"  {ts}  {label:<28} {tid:<12}{detail}")


def cmd_summary():
    queue = _load_queue()
    events = _load_events()

    if not queue:
        print("未找到 task_queue.json。")
        return

    tasks = queue.get("tasks", [])
    done_tasks   = [t for t in tasks if t["status"] == "DONE"]
    failed_tasks = [t for t in tasks if t["status"] == "FAILED"]
    pending_tasks= [t for t in tasks if t["status"] == "PENDING"]

    session_start = next((e for e in events if e["type"] == "session_start"), None)
    session_done  = next((e for e in reversed(events) if e["type"] == "session_done"), None)
    total_dur = _duration(
        session_start.get("ts") if session_start else None,
        session_done.get("ts")  if session_done  else None,
    )

    print(f"{BOLD}═══ 执行摘要 ══════════════════════════════════{RESET}")
    print(f"目标   : {queue['goal']}")
    print(f"会话   : {queue['session_id']}")
    print(f"总耗时 : {total_dur}")
    print(f"结果   : {_color(queue['status'], queue['status'])}")
    print()
    print(f"  完成  {len(done_tasks)}/{len(tasks)}")
    print(f"  失败  {len(failed_tasks)}/{len(tasks)}")
    print(f"  未执行 {len(pending_tasks)}/{len(tasks)}")

    if failed_tasks:
        print(f"\n{BOLD}失败任务：{RESET}")
        for t in failed_tasks:
            print(f"  [{t['id']}] {t['description']}")
            if t.get("result"):
                print(f"        原因: {t['result'][:120].replace(chr(10), ' ')}")

    if done_tasks:
        print(f"\n{BOLD}完成任务：{RESET}")
        for t in done_tasks:
            dur = _duration(t.get("started_at"), t.get("finished_at"))
            print(f"  [{t['id']}] ({dur}) {t['description']}")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--snapshot":
        cmd_snapshot()
    elif args[0] == "--watch":
        cmd_watch()
    elif args[0] == "--tail":
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30
        cmd_tail(n)
    elif args[0] == "--summary":
        cmd_summary()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
