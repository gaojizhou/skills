# Ollama Installation Guide

Use this reference when guiding a user to install Ollama locally (Step 4 of the skill).

---

## Detect the User's OS First

```bash
uname -s        # Linux / Darwin (macOS)
uname -m        # Architecture: x86_64 or arm64
sw_vers 2>/dev/null   # macOS version
lsb_release -a 2>/dev/null  # Linux distro
```

Or simply ask the user: "What operating system are you on? (macOS, Windows, or Linux)"

---

## macOS

```bash
# Option 1: Official installer (recommended)
# Direct the user to: https://ollama.com/download/mac
# They download and run the .dmg file.

# Option 2: Homebrew
brew install ollama
```

After install, Ollama runs as a menu bar app. To start from terminal:
```bash
ollama serve
```

---

## Linux

```bash
# One-line install (official)
curl -fsSL https://ollama.com/install.sh | sh

# Ollama will automatically set up a systemd service.
# Start it with:
sudo systemctl start ollama
sudo systemctl enable ollama   # auto-start on boot
```

Check status:
```bash
systemctl status ollama
curl http://localhost:11434/api/tags
```

---

## Windows

Direct the user to: **https://ollama.com/download/windows**

They download and run the `.exe` installer. Ollama runs as a background service after installation.

To verify in PowerShell:
```powershell
curl http://localhost:11434/api/tags
```

---

## After Installation — Pull a Model

Once Ollama is installed, the user needs at least one model. Suggest based on their task:

### General purpose (text tasks):
```bash
ollama pull llama3.2          # 2GB — small but capable
ollama pull mistral           # 4GB — good balance
ollama pull llama3.1:8b       # 5GB — solid all-rounder
ollama pull llama3.1:70b      # 40GB — powerful (needs strong GPU/RAM)
```

### Code tasks:
```bash
ollama pull qwen2.5-coder:7b  # 4.7GB — excellent code model
ollama pull deepseek-coder:6.7b
```

### Image / vision tasks:
```bash
ollama pull llava             # 4.7GB — standard vision model
ollama pull llava:13b         # 8GB — better quality
```

### Multilingual (including Chinese):
```bash
ollama pull qwen2.5:7b        # 4.7GB — strong multilingual
ollama pull qwen2.5:14b       # 9GB — better quality
```

---

## Hardware Recommendations

| RAM Available | Recommended Max Model Size |
|---|---|
| 8 GB | 3B–7B models (keep OS overhead in mind) |
| 16 GB | 7B–13B models comfortably |
| 32 GB | Up to 30B models |
| 64 GB+ | 70B models |

**GPU**: If the user has an NVIDIA or Apple Silicon GPU, Ollama will use it automatically for much faster inference.

---

## Verify Everything Works

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Quick test
ollama run llama3.2 "Say hello in one sentence."
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` on port 11434 | Run `ollama serve` in a terminal |
| Model not found | Run `ollama pull <model-name>` first |
| Very slow inference | No GPU detected; CPU-only mode. Consider a smaller model. |
| Out of memory | Model too large for available RAM. Try a smaller variant. |
| Windows: command not found | Restart terminal after installation |
