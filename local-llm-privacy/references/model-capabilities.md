# Model Capabilities Reference

A lookup table for common Ollama models. Use this to quickly assess what a model can and cannot do.

---

## Vision-Capable Models (can process images)

| Model | Min Size | Notes |
|---|---|---|
| llava | 7B | Most common vision model, general-purpose |
| llava:13b | 13B | Better quality than 7B |
| llava:34b | 34B | High quality |
| llava-llama3 | 8B | LLaMA 3 base, good balance |
| bakllava | 7B | Mistral base, alternative to llava |
| moondream | 1.8B | Tiny — simple image description only |
| minicpm-v | 8B | Strong for document/chart OCR |
| llava-phi3 | 3.8B | Phi-3 base, small but decent |
| cogvlm | 17B | Strong Chinese + English vision |

> moondream (1.8B) can describe images but fails at complex analysis, OCR, or multi-image reasoning.

---

## Code-Focused Models

| Model | Size | Strengths |
|---|---|---|
| codellama | 7B–34B | General code, Python/JS/C++ |
| codellama:python | 7B–34B | Python-specialized |
| deepseek-coder | 1.3B–33B | Excellent code quality |
| deepseek-coder-v2 | 16B–236B | State-of-art code model |
| qwen2.5-coder | 1.5B–72B | Strong multilingual code |
| starcoder2 | 3B–15B | Code completion |
| codegemma | 2B–7B | Google's code model |

---

## Embedding Models (NOT for generation)

These models output vectors, not text. Do NOT use for chat/generation tasks.

| Model | Notes |
|---|---|
| nomic-embed-text | Best general-purpose embeddings |
| mxbai-embed-large | High-quality, 334M |
| all-minilm | Tiny, fast, lower quality |
| snowflake-arctic-embed | Strong retrieval performance |
| bge-m3 | Multilingual embeddings |

---

## General Text Models

### Small (< 3B) — Simple tasks only
| Model | Params |
|---|---|
| qwen2:1.5b | 1.5B |
| phi3:mini | 3.8B |
| llama3.2:1b | 1B |
| tinyllama | 1.1B |

Cannot reliably handle: long documents, complex reasoning, structured JSON output, multi-step instructions.

### Medium (3B–8B) — Most everyday tasks
| Model | Params | Notes |
|---|---|---|
| llama3.2:3b | 3B | Good for its size |
| mistral:7b | 7B | Fast, solid baseline |
| llama3.1:8b | 8B | Recommended default text model |
| gemma2:9b | 9B | Strong |
| qwen2.5:7b | 7B | Strong multilingual |

### Large (13B–34B) — Professional tasks
| Model | Params |
|---|---|
| qwen2.5:14b | 14B |
| phi4 | 14B |
| mixtral:8x7b | ~47B MoE |
| codellama:34b | 34B |

### Very Large (70B+) — Near cloud quality
| Model | Params |
|---|---|
| llama3.1:70b | 70B |
| qwen2.5:72b | 72B |
| mixtral:8x22b | ~141B MoE |

---

## Task Recommendation Cheatsheet

| Task | Minimum | Recommended |
|---|---|---|
| Image description | moondream (1.8B) | llava:7b+ |
| Image OCR / document reading | minicpm-v (8B) | llava:13b |
| Short text summarization | 3B+ | llama3.1:8b |
| Long document summarization | 7B+ | llama3.1:8b+ |
| PII extraction / redaction | 7B+ | llama3.1:8b+ |
| Medical record parsing | 13B+ | llama3.1:70b |
| Code review | codellama:7b | deepseek-coder:7b+ |
| Complex reasoning | 13B+ | qwen2.5:14b+ |
| Translation | 7B+ | qwen2.5:7b+ |
| Embeddings / semantic search | nomic-embed-text | nomic-embed-text |
| Simple classification | 1.5B+ | phi3:mini or any 3B |
