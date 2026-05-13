import json
import requests
from pathlib import Path


def _load_config() -> dict:
    config_path = Path("config.json")
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text())


def _call_brain(prompt: str) -> str:
    config = _load_config()
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
    return response.json()["choices"][0]["message"]["content"]


def _parse_json(content: str) -> list:
    if "```" in content:
        content = content.split("```")[1].lstrip("json").strip()
    return json.loads(content)


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

    return _parse_json(_call_brain(prompt))


def is_complex(task_description: str) -> bool:
    config = _load_config()
    if config.get("brain_provider", "stub") == "stub":
        return False

    prompt = f"""判断以下任务是否过于复杂，无法由一个 AI 在单次对话中独立完成。
如果任务涉及多个不同技术模块、需要多个文件协同实现、或描述中包含"并且"/"同时"/"以及"等连接多个独立目标的词，则认为过于复杂。

任务：{task_description}

只回答 yes 或 no："""

    return _call_brain(prompt).strip().lower().startswith("yes")


def decompose_task(task_description: str, parent_id: str) -> list[dict]:
    config = _load_config()
    if config.get("brain_provider", "stub") == "stub":
        return [{"id": f"{parent_id}.1", "description": task_description, "depends_on": []}]

    prompt = f"""将以下任务分解为具体的可执行子任务。每个子任务必须足够简单，能由一个 AI 在单次对话中独立完成。

任务：{task_description}

只返回 JSON 数组，id 使用 {parent_id}.1、{parent_id}.2 等格式，不要其他文字：
[
  {{"id": "{parent_id}.1", "description": "完整的子任务描述", "depends_on": []}},
  {{"id": "{parent_id}.2", "description": "完整的子任务描述", "depends_on": ["{parent_id}.1"]}}
]"""

    return _parse_json(_call_brain(prompt))
