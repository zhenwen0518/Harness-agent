# Harness Agent

Break AI agents free from single-conversation limits. Automatically decompose complex goals into subtasks, execute them in parallel, and resume anytime after interruption.

Inspired by the Anthropic engineering blog: [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/research/scaling-managed-agents)

Video walkthrough (Chinese): [Bilibili](https://www.bilibili.com/video/BV1DB546wEb8)

---

## How It Works

```
You enter a goal
  └── Brain (any LLM) decomposes it into subtasks
        └── Complex subtasks are recursively split (up to 2 levels)
              └── Workers execute subtasks in parallel
                    └── Results are persisted locally — interrupt and resume anytime
```

Brain handles the thinking. Workers handle the doing. The two are fully decoupled and can each be swapped for any AI service independently.

---

## Quick Start

**Requirements:** Python 3.10+

```bash
git clone <repo-url>
cd harness-agent
pip install -r requirements.txt
cp config.example.json config.json
# Edit config.json and fill in your API keys
python3 harness.py "your goal"
```

---

## Configuration

`config.json` example (DeepSeek as Brain, Claude CLI as Worker):

```json
{
  "brain_provider": "openai_compatible",
  "brain_api_key": "your-deepseek-api-key",
  "brain_model": "deepseek-chat",
  "brain_base_url": "https://api.deepseek.com/v1",
  "worker_command": ["claude", "-p", "--dangerously-skip-permissions"],
  "max_parallel_workers": 3
}
```

Both Brain and Worker can be replaced independently. See [examples/README.md](examples/README.md) for all options.

---

## Usage

### Start a new task

```bash
python3 harness.py "your goal"
```

The program decomposes the goal and presents the task list for confirmation:

```
[Harness] Goal received: Build a Flask web app with user auth
[Harness] Analyzing goal...
[Harness] Tasks decomposed — please confirm:

  t1. Design database schema
  t2. Implement backend API        (depends on: t1)
  t3. Implement frontend           (depends on: t1)
  t4. Write integration tests      (depends on: t2, t3)

Proceed? (y/n): y

[Task t1] Starting: Design database schema...
[Task t1] ✓ Done
[Task t2] Starting: Implement backend API...
[Task t3] Starting: Implement frontend...     ← t2 and t3 run in parallel
[Task t2] ✓ Done
[Task t3] ✓ Done
[Task t4] Starting: Write integration tests...
[Task t4] ✓ Done

[Harness] All tasks complete. Events logged to session_store.jsonl
```

### Resume after interruption

Press `Ctrl+C` or close the terminal at any time. To continue:

```bash
python3 harness.py --resume
```

Completed tasks are skipped automatically. Execution picks up from where it left off.

---

## Pluggable AI Backends

Brain and Worker can each be replaced with any AI service:

| Role | Default | Alternatives |
|---|---|---|
| Brain (task decomposition) | DeepSeek | OpenAI, local Ollama, any OpenAI-compatible API |
| Worker (task execution) | Claude Code CLI | Anthropic SDK, OpenAI SDK, local models |

See [examples/README.md](examples/README.md) for setup instructions.

---

## Project Structure

```
├── harness.py                # Entry point, orchestration loop
├── brain.py                  # Brain: task decomposition and complexity check
├── worker.py                 # Worker: default CLI subprocess implementation
├── store.py                  # Persistence layer
├── config.example.json       # Configuration template
├── examples/
│   ├── README.md                       # Worker integration guide
│   ├── worker_anthropic_sdk.py         # Worker: Anthropic Python SDK
│   └── worker_openai_compatible.py     # Worker: OpenAI-compatible API
└── tests/
```

Generated at runtime (excluded via .gitignore):
- `task_queue.json` — task state machine
- `session_store.jsonl` — event log

---

## Good Use Cases

- Writing code, generating files, running scripts — anything that can be broken into steps
- Long-running tasks that may be interrupted
- Tasks that benefit from multiple AI workers running in parallel

## Not Suitable For

- Interactive tasks that require human input mid-execution
- Subtasks that need to share in-memory state (each Worker is an independent process)

---

---

# Harness Agent（中文说明）

让 AI Agent 突破单次对话的限制。把复杂目标自动拆解为子任务，并行执行，支持随时中断续接。

灵感来源：Anthropic 工程博客 [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/research/scaling-managed-agents)

视频介绍：[Bilibili](https://www.bilibili.com/video/BV1DB546wEb8)

---

## 工作原理

```
你输入目标
  └── Brain（任意 LLM）把目标拆解成子任务
        └── 复杂的子任务自动继续拆分（最多 2 层）
              └── Workers 并行执行每个子任务
                    └── 结果持久化到本地，随时中断续接
```

Brain 负责"想"，Worker 负责"做"，两者完全解耦，可以独立替换为任意 AI 服务。

---

## 快速开始

**环境要求：** Python 3.10+

```bash
git clone <repo-url>
cd harness-agent
pip install -r requirements.txt
cp config.example.json config.json
# 编辑 config.json，填入你的 API Key
python3 harness.py "你的目标"
```

---

## 配置

`config.json` 示例（DeepSeek 作为 Brain，Claude CLI 作为 Worker）：

```json
{
  "brain_provider": "openai_compatible",
  "brain_api_key": "your-deepseek-api-key",
  "brain_model": "deepseek-chat",
  "brain_base_url": "https://api.deepseek.com/v1",
  "worker_command": ["claude", "-p", "--dangerously-skip-permissions"],
  "max_parallel_workers": 3
}
```

Brain 和 Worker 可以独立替换，详见 [examples/README.md](examples/README.md)。

---

## 使用

### 启动新任务

```bash
python3 harness.py "你的目标"
```

程序会拆解任务、展示列表，输入 `y` 确认执行：

```
[Harness] Goal received: 写一个 Flask Web 应用，支持用户注册登录
[Harness] Analyzing goal...
[Harness] Tasks decomposed — please confirm:

  t1. 设计数据库 schema
  t2. 实现后端 API          (depends on: t1)
  t3. 实现前端页面          (depends on: t1)
  t4. 写集成测试            (depends on: t2, t3)

Proceed? (y/n): y

[Task t1] ✓ Done
[Task t2] Starting: 实现后端 API...
[Task t3] Starting: 实现前端页面...     ← t2 和 t3 并行
[Task t2] ✓ Done
[Task t3] ✓ Done
[Task t4] ✓ Done

[Harness] All tasks complete. Events logged to session_store.jsonl
```

### 中断后续接

任何时候按 `Ctrl+C` 或关掉终端，下次运行：

```bash
python3 harness.py --resume
```

已完成的任务自动跳过，从中断处继续。

---

## 接入不同 AI 服务

Brain 和 Worker 可以独立替换：

| 角色 | 默认 | 可替换为 |
|---|---|---|
| Brain（任务拆解） | DeepSeek | OpenAI、本地 Ollama、任意 OpenAI 兼容 API |
| Worker（任务执行） | Claude Code CLI | Anthropic SDK、OpenAI SDK、本地模型 |

详见 [examples/README.md](examples/README.md)。

---

## 项目结构

```
├── harness.py                # 主入口，编排调度逻辑
├── brain.py                  # Brain：任务拆解与复杂度判断
├── worker.py                 # Worker：默认 CLI subprocess 实现
├── store.py                  # 持久化读写
├── config.example.json       # 配置模板
├── examples/
│   ├── README.md                       # Worker 接入指南
│   ├── worker_anthropic_sdk.py         # Worker：Anthropic Python SDK
│   └── worker_openai_compatible.py     # Worker：OpenAI 兼容 API
└── tests/
```

运行时生成（已加入 .gitignore）：
- `task_queue.json` — 任务状态机
- `session_store.jsonl` — 事件日志

---

## 适合的场景

- 写代码、生成文件、执行脚本等可拆分的任务
- 需要长时间执行、可能中断的任务
- 希望多个 AI Worker 并行分工的场景

## 不适合的场景

- 需要中途人工介入的交互式任务
- 子任务之间需要共享内存状态（每个 Worker 是独立进程）
