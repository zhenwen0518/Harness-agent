import json
import requests
from pathlib import Path


def _load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text())


def decompose_goal(goal: str) -> list[dict]:
    config = _load_config()

    if config.get("brain_provider", "stub") == "stub":
        return [{"id": "t1", "description": goal, "depends_on": []}]

    prompt = f"""将以下目标分解为具体的可执行子任务列表。每个子任务将由 Claude Code 独立执行。

目标：{goal}

只返回 JSON 数组，不要其他文字：
[
  {{"id": "t1", "description": "完整的子任务描述", "depends_on": []}},
  {{"id": "t2", "description": "完整的子任务描述", "depends_on": ["t1"]}}
]"""

    response = requests.post(
        f"{config['brain_base_url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {config['brain_api_key']}",
            "Content-Type": "application/json"
        },
        json={
            "model": config["brain_model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        },
        timeout=60
    )

    content = response.json()["choices"][0]["message"]["content"]

    if "```" in content:
        content = content.split("```")[1].lstrip("json").strip()

    return json.loads(content)
