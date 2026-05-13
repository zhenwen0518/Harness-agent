# Harness Agent

让 AI Agent 突破单次对话限制，把复杂目标拆解为子任务并行执行，支持随时中断续接。

灵感来源：Anthropic 工程博客 [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/research/scaling-managed-agents)

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
├── harness.py       # 主入口，编排调度逻辑
├── brain.py         # 任务拆解（DeepSeek API）
├── worker.py        # Worker 封装（claude -p subprocess）
├── store.py         # 持久化读写
├── config.json      # 配置文件
├── task_queue.json  # 运行时生成
└── session_store.jsonl  # 运行时生成
```
