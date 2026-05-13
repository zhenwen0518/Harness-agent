"""
Worker: OpenAI-compatible API

Works with:
- OpenAI (GPT-4o, o3)
- Groq (llama, mixtral — very fast)
- Local models via Ollama or LM Studio (set base_url to http://localhost:11434/v1)
- Any service supporting the OpenAI Chat Completions format

Usage:
  Replace worker.py with this file, or update the import in harness.py:
  from examples.worker_openai_compatible import run_worker

Add to config.json:
  "worker_api_key": "your-api-key",
  "worker_model": "gpt-4o",
  "worker_base_url": "https://api.openai.com/v1"   (for local Ollama: http://localhost:11434/v1)
"""

import json
from openai import OpenAI
from pathlib import Path


def _load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text())


def run_worker(task_description: str, worker_command: list[str] | None = None) -> tuple[bool, str]:
    config = _load_config()

    client = OpenAI(
        api_key=config.get("worker_api_key", "ollama"),
        base_url=config.get("worker_base_url", "https://api.openai.com/v1")
    )

    try:
        response = client.chat.completions.create(
            model=config.get("worker_model", "gpt-4o"),
            messages=[{"role": "user", "content": task_description}]
        )
        return True, response.choices[0].message.content
    except Exception as e:
        return False, str(e)
