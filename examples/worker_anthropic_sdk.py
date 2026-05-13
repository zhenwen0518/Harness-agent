"""
Worker: Anthropic Python SDK（直接 API，无需安装 Claude CLI）

适合场景：
- 没有安装 Claude Code CLI
- 需要精确控制 token 用量
- 任务是纯文本生成（不需要执行代码、写文件）

使用方法：
  将 worker.py 替换为本文件，或在 harness.py 中修改导入：
  from examples.worker_anthropic_sdk import run_worker

config.json 需要增加：
  "worker_api_key": "your-anthropic-api-key",
  "worker_model": "claude-opus-4-7"
"""

import json
import anthropic
from pathlib import Path


def _load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text())


def run_worker(task_description: str, worker_command: list[str] | None = None) -> tuple[bool, str]:
    config = _load_config()

    client = anthropic.Anthropic(api_key=config.get("worker_api_key"))

    try:
        message = client.messages.create(
            model=config.get("worker_model", "claude-opus-4-7"),
            max_tokens=8096,
            messages=[{"role": "user", "content": task_description}]
        )
        return True, message.content[0].text
    except Exception as e:
        return False, str(e)
