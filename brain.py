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

    prompt = f"""Decompose the following goal into a list of concrete, executable subtasks. Each subtask will be executed independently by an AI agent.

Goal: {goal}

Return only a JSON array, no other text:
[
  {{"id": "t1", "description": "full subtask description", "depends_on": []}},
  {{"id": "t2", "description": "full subtask description", "depends_on": ["t1"]}}
]"""

    return _parse_json(_call_brain(prompt))


def is_complex(task_description: str) -> bool:
    config = _load_config()
    if config.get("brain_provider", "stub") == "stub":
        return False

    prompt = f"""Determine whether the following task is too complex to be completed by a single AI agent in one conversation.
Consider it too complex if it involves multiple distinct technical components, requires coordinating multiple files, or contains conjunctions like "and also" / "as well as" that suggest multiple independent goals.

Task: {task_description}

Reply with only yes or no:"""

    return _call_brain(prompt).strip().lower().startswith("yes")


def decompose_task(task_description: str, parent_id: str) -> list[dict]:
    config = _load_config()
    if config.get("brain_provider", "stub") == "stub":
        return [{"id": f"{parent_id}.1", "description": task_description, "depends_on": []}]

    prompt = f"""Break down the following task into smaller subtasks. Each subtask must be simple enough for a single AI agent to complete in one conversation.

Task: {task_description}

Return only a JSON array using {parent_id}.1, {parent_id}.2, etc. as IDs, no other text:
[
  {{"id": "{parent_id}.1", "description": "full subtask description", "depends_on": []}},
  {{"id": "{parent_id}.2", "description": "full subtask description", "depends_on": ["{parent_id}.1"]}}
]"""

    return _parse_json(_call_brain(prompt))
