# Worker 接入示例

Harness Agent 的 Worker 层是可替换的。默认用 `claude -p`（Claude Code CLI），以下是其他接入方式。

---

## 方式一：Claude Code CLI（默认）

**适合：** 需要执行代码、读写文件、运行命令的复杂任务

```json
// config.json
{
  "worker_command": ["claude", "-p", "--dangerously-skip-permissions"]
}
```

Worker 以子进程方式启动 Claude Code，拥有完整的工具调用能力（写文件、执行 Bash、搜索代码等），是最强的 Worker 形态。

---

## 方式二：Anthropic SDK（`worker_anthropic_sdk.py`）

**适合：** 没有安装 Claude CLI、纯文本生成任务、需要控制 token 用量

```json
// config.json
{
  "worker_api_key": "your-anthropic-api-key",
  "worker_model": "claude-opus-4-7"
}
```

```python
# harness.py 顶部修改导入
from examples.worker_anthropic_sdk import run_worker
```

注意：此模式下 Worker 只能生成文本，无法直接操作文件系统。

---

## 方式三：OpenAI 兼容 API（`worker_openai_compatible.py`）

**适合：** 使用 GPT-4o、Groq、本地模型（Ollama）等

```json
// config.json — OpenAI
{
  "worker_api_key": "your-openai-api-key",
  "worker_model": "gpt-4o",
  "worker_base_url": "https://api.openai.com/v1"
}

// config.json — 本地 Ollama
{
  "worker_api_key": "ollama",
  "worker_model": "llama3.2",
  "worker_base_url": "http://localhost:11434/v1"
}
```

```python
# harness.py 顶部修改导入
from examples.worker_openai_compatible import run_worker
```

---

## 切换 Worker 的方法

在 `harness.py` 第 9 行修改导入：

```python
# 默认（Claude CLI）
from worker import run_worker

# 改成 Anthropic SDK
from examples.worker_anthropic_sdk import run_worker

# 改成 OpenAI 兼容
from examples.worker_openai_compatible import run_worker
```

---

## Brain 也可以替换

Brain（任务拆解）目前使用 DeepSeek，但因为走的是 OpenAI 兼容格式，任何支持该格式的模型都可以接入，只需修改 `config.json`：

```json
// 换成 OpenAI
{
  "brain_api_key": "your-openai-api-key",
  "brain_model": "gpt-4o",
  "brain_base_url": "https://api.openai.com/v1"
}

// 换成本地 Ollama
{
  "brain_api_key": "ollama",
  "brain_model": "llama3.2",
  "brain_base_url": "http://localhost:11434/v1"
}
```
