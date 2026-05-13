# Worker Integration Examples

The Worker layer in Harness Agent is pluggable. The default uses `claude -p` (Claude Code CLI). Below are alternative integrations.

---

## Option 1: Claude Code CLI (default)

**Best for:** Tasks that require executing code, reading/writing files, or running shell commands

```json
// config.json
{
  "worker_command": ["claude", "-p", "--dangerously-skip-permissions"]
}
```

Workers spawn Claude Code as a subprocess with full tool access (file writes, Bash execution, code search, etc.). This is the most capable Worker option.

---

## Option 2: Anthropic SDK (`worker_anthropic_sdk.py`)

**Best for:** No Claude CLI installed, pure text generation, fine-grained token control

```json
// config.json
{
  "worker_api_key": "your-anthropic-api-key",
  "worker_model": "claude-opus-4-7"
}
```

```python
# Update the import at the top of harness.py
from examples.worker_anthropic_sdk import run_worker
```

Note: In this mode, Workers can only generate text — they cannot directly access the file system.

---

## Option 3: OpenAI-compatible API (`worker_openai_compatible.py`)

**Best for:** GPT-4o, Groq, or local models via Ollama

```json
// config.json — OpenAI
{
  "worker_api_key": "your-openai-api-key",
  "worker_model": "gpt-4o",
  "worker_base_url": "https://api.openai.com/v1"
}

// config.json — Local Ollama
{
  "worker_api_key": "ollama",
  "worker_model": "llama3.2",
  "worker_base_url": "http://localhost:11434/v1"
}
```

```python
# Update the import at the top of harness.py
from examples.worker_openai_compatible import run_worker
```

---

## How to Switch Workers

Edit line 9 of `harness.py`:

```python
# Default (Claude CLI)
from worker import run_worker

# Anthropic SDK
from examples.worker_anthropic_sdk import run_worker

# OpenAI-compatible
from examples.worker_openai_compatible import run_worker
```

---

## Replacing the Brain

The Brain (task decomposition) uses DeepSeek by default, but any OpenAI-compatible model works. Just update `config.json`:

```json
// OpenAI
{
  "brain_api_key": "your-openai-api-key",
  "brain_model": "gpt-4o",
  "brain_base_url": "https://api.openai.com/v1"
}

// Local Ollama
{
  "brain_api_key": "ollama",
  "brain_model": "llama3.2",
  "brain_base_url": "http://localhost:11434/v1"
}
```
