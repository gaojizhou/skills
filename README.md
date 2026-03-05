# Code Skills

A collection of automation skills for OpenClaw / Claude.

## Overview

This repository contains three standalone utility modules for automating common tasks:

| Skill | Description | Dependencies |
|-------|-------------|--------------|
| `epub` | Process EPUB ebooks (extract TOC, metadata, chapters) | beautifulsoup4, lxml |
| `phone-agent` | Control Android devices via natural language | AutoGLM SDK |
| `totp` | Manage TOTP two-factor authentication codes | None (stdlib only) |

## Quick Start

```bash
# Install dependencies
pip install beautifulsoup4 lxml

# TOTP - Create a new 2FA account
python3 totp/scripts/totp_manager.py create "GitHub" --issuer "GitHub"

# TOTP - Get current code
python3 totp/scripts/totp_manager.py code "GitHub"
```

## Skills

### EPUB
Parse EPUB files without specialized libraries. Uses unzip + standard parsing.

- Extract table of contents (nav.xhtml / toc.ncx)
- Read metadata (title, author, publisher)
- Extract chapter text (HTML → plain text)
- Repack modified EPUBs

### Phone Agent
Android device automation via [AutoGLM Phone Agent](https://github.com/THUDM/AutoGLM).

- Natural language UI control (tap, swipe, type, screenshot)
- App automation testing
- End-to-end user journey reproduction

Requires: Android device with USB debugging, `adb`, and running Phone Agent backend.

### TOTP
Pure Python TOTP implementation (RFC 6238 / RFC 4226). Zero dependencies.

- Generate TOTP secrets and codes
- Import existing Base32 keys
- Compatible with Google Authenticator, Authy, 1Password
- Secure storage at `~/.totp_secrets.json` (permission 600)

## Usage Examples

**TOTP Python API:**
```python
import sys
sys.path.insert(0, "totp/scripts")
from totp_manager import create_new_totp, get_current_code

# Create account
result = create_new_totp("GitHub", issuer="GitHub")
print(f"Secret: {result['secret']}")
print(f"Code: {result['current_code']}")

# Get current code
code = get_current_code("GitHub")
print(f"Current: {code['code']} (expires in {code['remaining_seconds']}s)")
```

**Phone Agent:**
```python
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig

model = ModelConfig(
    base_url="https://open.bigmodel.cn/api/paas/v4",
    model_name="autoglm-phone",
    api_key="your-key"
)
agent = PhoneAgent(model_config=model)
agent.run("Open Play Store, search for Signal, and install it")
```

## Security Notes

- TOTP secrets are stored in plaintext at `~/.totp_secrets.json` — back them up securely
- Use Phone Agent only on test devices, not production systems
- Keep your API keys private and out of version control

## License

MIT
