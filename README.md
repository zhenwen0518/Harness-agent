# Harness Agent

让 AI Agent 突破单次对话限制，把复杂目标拆解为子任务并行执行，支持随时中断续接。

灵感来源：Anthropic 工程博客 [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/research/scaling-managed-agents)

Bilibili up主：小天fotos  
https://www.bilibili.com/video/BV1DB546wEb8?buvid=YB469CB6996DD13F40D59A4DC7656AB842FE&from_spmid=main.my-fav.0.0&is_story_h5=false&mid=UEemUv4BZmXFKc3JIM851g%3D%3D&plat_id=114&share_from=ugc&share_medium=iphone&share_plat=ios&share_session_id=4820DD47-6017-48A9-A140-52DEB90AF283&share_source=WEIXIN&share_tag=s_i&timestamp=1778604771&unique_k=HNlLsR7&up_id=28554995

---

## 工作原理

```
你输入目标
  └── Brain（DeepSeek）把目标拆解成子任务
        └── 复杂的子任务自动继续拆分（最多 2 层）
              └── Workers（Claude Code）并行执行每个子任务
                    └── 所有结果持久化到本地文件，随时可中断续接
```

---

## 环境要求

- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) —— Worker 执行引擎，需登录 Claude 账号
- DeepSeek API Key —— Brain 任务拆解，[申请地址](https://platform.deepseek.com/)

---

## 安装

```bash
git clone <repo-url>
cd "Harness agent"
pip install -r requirements.txt
```

---

## 配置

复制并编辑 `config.json`：

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

| 字段 | 说明 |
|---|---|
| `brain_api_key` | DeepSeek API Key |
| `brain_model` | 拆解任务用的模型，默认 `deepseek-chat` |
| `max_parallel_workers` | 最多同时运行几个 Worker，默认 3 |
| `worker_command` | Worker 执行命令，默认用本地 Claude Code CLI |

Brain 和 Worker 可以独立替换为其他 AI 服务，详见 [examples/README.md](examples/README.md)。

---

## 使用

### 启动新任务

```bash
python3 harness.py "你的目标"
```

示例：

```bash
python3 harness.py "写一个 Flask Web 应用，支持用户注册登录，数据存到 SQLite"
```

程序会：
1. 调用 DeepSeek 把目标拆解成子任务
2. 展示任务列表，等待确认
3. 输入 `y` 开始执行，`n` 取消

### 中断后续接

任何时候按 `Ctrl+C` 或关掉终端，下次运行：

```bash
python3 harness.py --resume
```

已完成的任务自动跳过，从中断处继续。

### 实时监控面板（内置）

harness 运行时会自动在同一个终端实时刷新任务状态，无需另开窗口：

```
目标：写一个 Flask Web 应用，支持用户注册登录
进度：2/4 完成  1 运行中  0 失败

ID         状态       耗时   描述
────────────────────────────────────────────────────────────────────────
t1         ✓ DONE     12s    设计数据库 schema
t2         ◉ RUNNING  8s     实现后端 API
t3         ○ PENDING  -      实现前端页面
t4         ○ PENDING  -      写集成测试
```

每当有任务启动、完成或失败，面板自动清屏刷新。

### 事后查询（monitor.py）

任务结束后，可用 `monitor.py` 做进一步分析：

```bash
python3 monitor.py              # 快照：当前任务状态表格
python3 monitor.py --tail       # 日志流：显示最近 30 条事件
python3 monitor.py --tail 50    # 日志流：显示最近 N 条事件
python3 monitor.py --summary    # 摘要报告：耗时、成功/失败统计、错误详情
```

---

## 任务状态

运行时会生成两个文件：

- `task_queue.json` —— 任务状态机，记录每个子任务的执行状态和结果
- `session_store.jsonl` —— 事件日志，每行一条记录

任务状态：`PENDING` → `RUNNING` → `DONE` / `FAILED`

---

## 适合的场景

- 写代码、生成文件、执行脚本
- 可以拆成多个独立步骤的任务
- 需要长时间执行、可能中断的任务

## 不适合的场景

- 需要中途人工介入的交互式任务
- 子任务之间需要共享内存状态（每个 Worker 是独立进程）

---

## 项目结构

```
├── harness.py                # 主入口，编排调度逻辑
├── monitor.py                # 监控工具：实时状态、事件日志、执行摘要
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

---

# Harness Agent (English)

Break AI agents free from single-conversation limits. Automatically decompose complex goals into subtasks, execute them in parallel, and resume anytime after interruption.

Inspired by the Anthropic engineering blog: [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/research/scaling-managed-agents)

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

## Usage

### Start a new task

```bash
python3 harness.py "your goal"
```

### Resume after interruption

```bash
python3 harness.py --resume
```

### Built-in live dashboard

Harness renders a task status table in the same terminal, refreshing automatically on every state change — no second terminal needed.

### Post-run analysis (monitor.py)

```bash
python3 monitor.py              # Snapshot: current task status table
python3 monitor.py --tail       # Tail: stream the last 30 event log entries
python3 monitor.py --tail 50    # Tail: show last N entries
python3 monitor.py --summary    # Summary: timing, pass/fail counts, error details
```

---

## Pluggable AI Backends

| Role | Default | Alternatives |
|---|---|---|
| Brain (task decomposition) | DeepSeek | OpenAI, local Ollama, any OpenAI-compatible API |
| Worker (task execution) | Claude Code CLI | Anthropic SDK, OpenAI SDK, local models |

See [examples/README.md](examples/README.md) for setup instructions.
