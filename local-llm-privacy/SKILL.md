---
name: local-llm-privacy
description: >
  Use this skill whenever the user has privacy-sensitive data they do NOT want sent to the cloud/network,
  and needs AI assistance processing it locally. Trigger on phrases like: "don't want to upload this",
  "process locally", "private data", "sensitive files", "keep it offline", "confidential documents",
  "local model", "run on my machine", "no internet", "air-gapped", "HIPAA", "PII", "personal information",
  "can't share this externally", "use ollama", "use local AI", or any situation where the user expresses
  concern about data leaving their machine. Also trigger when a user shares something clearly sensitive
  (medical records, financial data, personal ID info, internal company data) and asks for AI processing.
  This skill routes the task to a local Ollama model when available, handles model capability matching,
  and gracefully falls back to asking the user if they'd like to install Ollama or proceed with cloud.
---

# Local LLM Privacy Skill

Handle AI tasks involving private or sensitive data by routing them to a **local Ollama model** instead of the cloud. This protects user data by never sending it to external APIs.

---

## Step 1 — Confirm the Privacy Requirement

Before doing anything, acknowledge why local processing matters here. Say something like:

> "Since this data is sensitive, I'll try to handle it using a local model on your machine so nothing gets sent to the cloud."

Then proceed to Step 2.

---

## Step 2 — Detect Ollama and Available Models

Run the following bash commands to check for Ollama:

```bash
# Check if ollama is installed and running
ollama list 2>/dev/null || echo "OLLAMA_NOT_FOUND"
```

Parse the output into three possible states:

| State | Condition |
|-------|-----------|
| **A — Available** | `ollama list` returns a model list |
| **B — Installed but not running** | `ollama` command exists but connection refused → try `ollama serve &` then retry |
| **C — Not installed** | `OLLAMA_NOT_FOUND` or command not found |

---

## Step 3 — Model Selection (State A: Ollama running)

Read the model list carefully. Select the **best available model** for the task using the capability matrix below. If multiple models qualify, prefer larger/more capable ones.

Consult `references/model-capabilities.md` for the full model reference table.

### 3a. Task Type — Check First

Some models simply cannot do certain tasks regardless of size:

- **Image/vision tasks** → requires a vision-capable model (llava, bakllava, moondream, minicpm-v, etc.).
  A text-only model (mistral, llama, phi, gemma, qwen text variants) **cannot** process images — tell the user immediately.
- **Code generation** → prefer codellama, deepseek-coder, qwen2.5-coder, starcoder
- **Embeddings/semantic search** → prefer nomic-embed-text, mxbai-embed, all-minilm
- **General text** → any instruct/chat model works

### 3b. Model Size — Check Second

Larger = more capable for complex tasks:

| Size Range | Example Models | Suitable For |
|---|---|---|
| < 3B | phi3:mini, qwen2:1.5b, smollm | Simple Q&A, short summaries, keyword extraction only |
| 3B–7B | phi3:medium, llama3.2:3b, mistral:7b | Summaries, classification, basic analysis |
| 8B–13B | llama3.1:8b, mistral-nemo | Most professional tasks, structured extraction, code review |
| 14B–34B | qwen2.5:14b, codellama:34b | Complex reasoning, nuanced writing, long documents |
| 70B+ | llama3.1:70b, qwen2.5:72b | Near cloud-quality, nearly any text task |

**Infer size from model name tag**: `:1b`/`:2b` → tiny, `:7b`/`:8b` → medium, `:13b`/`:14b` → large, `:70b`/`:72b` → very large. No tag or `:latest` → assume default for that family (usually 7–8B).

### 3c. When No Good Match Exists

If models are **too small** for the task:

> "Your available local model (`{model_name}`, ~{size}B params) may struggle with this task because {reason}. Results may be incomplete or unreliable. Options: proceed anyway, pull a larger model (`ollama pull llama3.1:8b`), or use a cloud model."

If task needs **vision** but no vision model exists:

> "This task involves images, but none of your local models support vision. Run `ollama pull llava` or `ollama pull moondream` to process images locally. Or I can use a cloud model if you consent."

---

## Step 4 — Call the Local Model

Once a model is selected, send the task via the Ollama REST API:

**Text generation:**
```bash
curl -s http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<selected_model>",
    "prompt": "<constructed_prompt>",
    "stream": false
  }'
```

**Chat-style (with history):**
```bash
curl -s http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<selected_model>",
    "messages": [{"role": "user", "content": "<prompt>"}],
    "stream": false
  }'
```

**Vision tasks** (vision model required):
```bash
BASE64_IMG=$(base64 -w 0 /path/to/image.jpg)
curl -s http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llava\",
    \"prompt\": \"<prompt>\",
    \"images\": [\"$BASE64_IMG\"],
    \"stream\": false
  }"
```

Parse `.response` (or `.message.content` for chat) from the JSON output and present it to the user.

---

## Step 5 — Fallback Flows

### State B — Ollama installed but not running

```bash
ollama serve > /tmp/ollama.log 2>&1 &
sleep 3
ollama list
```

If it starts, continue from Step 3. If it fails, treat as State C.

### State C — Ollama not installed

Present the user with explicit choices — **do not proceed with cloud without consent**:

> "Ollama doesn't appear to be installed, so I can't process your data locally right now. Here are your options:
>
> 1. **Install Ollama** — Visit https://ollama.com/download (~2 min setup). Then come back and I'll use it automatically.
> 2. **Pull a model after install** — `ollama pull llama3.1:8b` (text) or `ollama pull llava` (vision)
> 3. **Use a cloud model** — I can process this with my standard capabilities, but the data will leave your device.
>
> Which would you prefer?"

---

## Step 6 — Output and Transparency

After every local processing run, always disclose:
- Which model was used (e.g., `llama3.1:8b`)
- That it ran locally / or that cloud was used (with user consent)
- Any quality caveats from model size limitations

Example footer:
> *Processed locally using `mistral:7b` on your machine. No data was sent to any external server.*

---

## Quick Reference

| Scenario | Action |
|---|---|
| Has `llava` / `moondream` | Use for image tasks |
| Has `llama3.1:8b`+ | Good for most text tasks |
| Has only tiny model (< 3B) | Warn: simple tasks only |
| Has `nomic-embed-text` only | Embeddings only, not generation |
| Has `deepseek-coder` / `qwen2.5-coder` | Prefer for code tasks |
| No Ollama installed | Offer install guide or cloud opt-in |
| Vision task, no vision model | Explain gap, suggest `ollama pull llava` |

---

## Core Rules

- **Never silently fall back to cloud** — always ask first and get explicit consent.
- **Never assume a text model can do vision** — check model family name before attempting.
- **Small model failures are silent** — if output looks garbled/truncated, tell user and suggest a larger model.
- **Privacy guarantee** — when local processing succeeds, confirm data stayed on-device.
