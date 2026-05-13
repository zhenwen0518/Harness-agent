"""
Worker: Anthropic Python SDK (direct API, no Claude CLI required)

Best for:
- Environments without Claude Code CLI installed
- Pure text generation tasks (no file system access needed)
- Fine-grained token usage control

Usage:
  Replace worker.py with this file, or update the import in harness.py:
  from examples.worker_anthropic_sdk import run_worker

Add to config.json:
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
