# Harness Agent

让 AI Agent 突破单次对话的限制。把复杂目标自动拆解为子任务，并行执行，支持随时中断续接。

灵感来源：Anthropic 工程博客 [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/research/scaling-managed-agents)

---

## 工作原理

```
你输入目标
  └── Brain（任意 LLM）把目标拆解成子任务
        └── 复杂的子任务自动继续拆分（最多 2 层）
              └── Workers（并行）执行每个子任务
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
[Harness] 收到目标：写一个 Flask Web 应用，支持用户注册登录
[Harness] 正在分析目标...
[Harness] 拆解出以下任务，请确认：

  t1. 设计数据库 schema
  t2. 实现后端 API          (依赖: t1)
  t3. 实现前端页面          (依赖: t1)
  t4. 写集成测试            (依赖: t2, t3)

确认执行？(y/n): y

[Task t1] 开始：设计数据库 schema...
[Task t1] ✓ 完成
[Task t2] 开始：实现后端 API...
[Task t3] 开始：实现前端页面...     ← t2 和 t3 并行
[Task t2] ✓ 完成
[Task t3] ✓ 完成
[Task t4] 开始：写集成测试...
[Task t4] ✓ 完成

[Harness] 全部完成。事件记录于 session_store.jsonl
```

### 中断后续接

任何时候 `Ctrl+C` 或关掉终端，下次运行：

```bash
python3 harness.py --resume
```

已完成的任务自动跳过，从中断处继续。

---

## 接入不同 AI 服务

Brain 和 Worker 可以独立替换为任意服务：

| 角色 | 默认 | 可替换为 |
|---|---|---|
| Brain（任务拆解） | DeepSeek | OpenAI、本地 Ollama、任意 OpenAI 兼容 API |
| Worker（任务执行） | Claude Code CLI | Anthropic SDK、OpenAI SDK、本地模型 |

详细说明和配置示例见 [examples/README.md](examples/README.md)。

---

## 项目结构

```
├── harness.py                # 主入口，编排调度逻辑
├── brain.py                  # Brain：任务拆解与复杂度判断
├── worker.py                 # Worker：默认 CLI subprocess 实现
├── store.py                  # 持久化读写
├── config.example.json       # 配置模板
├── examples/
│   ├── README.md             # Worker 接入指南
│   ├── worker_anthropic_sdk.py     # Worker：Anthropic Python SDK
│   └── worker_openai_compatible.py # Worker：OpenAI 兼容 API
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
