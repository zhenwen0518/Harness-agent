"""
Worker: OpenAI 兼容 API

适合接入：
- OpenAI（GPT-4o、o3）
- Groq（llama、mixtral，速度极快）
- 本地模型（Ollama、LM Studio，base_url 改成 http://localhost:11434/v1）
- 任何支持 OpenAI Chat Completions 格式的服务

使用方法：
  将 worker.py 替换为本文件，或在 harness.py 中修改导入：
  from examples.worker_openai_compatible import run_worker

config.json 需要增加：
  "worker_api_key": "your-api-key",
  "worker_model": "gpt-4o",
  "worker_base_url": "https://api.openai.com/v1"   （本地模型改成 http://localhost:11434/v1）
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
