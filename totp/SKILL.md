---
name: totp
description: Manage Time-based One-Time Passwords (TOTP / Two-Factor Authentication / 2FA / MFA). This skill must be used whenever the user needs to create, generate, read, import, or manage TOTP verification codes. Trigger scenarios include: "help me set up two-factor authentication", "generate a TOTP key", "I need a 2FA code", "set up Google Authenticator", "generate a one-time password", "view my verification code", and any request involving TOTP / OTP / two-step verification / Multi-Factor Authentication (MFA). Even if the user simply says "help me add verification", this skill should be triggered.
---

## Core Script

Path: `/mnt/skills/user/totp/scripts/totp_manager.py` (after installation)
Development/testing path: `scripts/totp_manager.py`

**Before first use**, confirm the script is executable:
```bash
python3 /path/to/totp_manager.py list
```

---

## Storage Location

Keys are saved by default in the user's home directory: `~/.totp_secrets.json` (permission 600, owner-readable only)

---

## Standard Workflows

### 1. Create a New TOTP Account (Most Common)

When the user says "help me set up two-factor authentication":

```bash
python3 scripts/totp_manager.py create "<account_name>" --issuer "<service_name>"
```

Example JSON response:
```json
{
  "name": "GitHub",
  "secret": "JBSWY3DPEHPK3PXP",
  "issuer": "GitHub",
  "otpauth_uri": "otpauth://totp/GitHub:GitHub?secret=...",
  "current_code": "123456",
  "remaining_seconds": 22,
  "storage_path": "/root/.totp_secrets.json"
}
```

**When presenting to the user, you must include:**
- ✅ Current 6-digit code and remaining seconds
- ✅ Base32 secret (for importing into an Authenticator App)
- ✅ `otpauth://` URI (can be used to generate a QR code)
- ✅ Storage path

---

### 2. Get the Current Code for a Saved Account

```bash
python3 scripts/totp_manager.py code "<account_name>"
```

If the account does not exist, return an error message guiding the user to create it first.

---

### 3. Import an Existing Key

When the user already has a Base32 secret (e.g., migrating from another Authenticator):

```bash
python3 scripts/totp_manager.py import "<account_name>" "<Base32_secret>" --issuer "<service_name>"
```

---

### 4. List All Accounts

```bash
python3 scripts/totp_manager.py list
```

---

### 5. Delete an Account

```bash
python3 scripts/totp_manager.py delete "<account_name>"
```

---

## Calling via bash_tool (How Claude Actually Uses It)

Claude should execute the above commands via `bash_tool`. Example:

```python
# Create a new account
bash_tool(
    command="python3 /mnt/skills/user/totp/scripts/totp_manager.py create 'GitHub' --issuer 'GitHub'",
    description="Create a GitHub TOTP two-factor authentication key"
)

# Get the current code
bash_tool(
    command="python3 /mnt/skills/user/totp/scripts/totp_manager.py code 'GitHub'",
    description="Read the current GitHub TOTP verification code"
)
```

---

## Standard Reply Format for Users

After successful creation, Claude should display in a clear format:

```
✅ TOTP two-factor authentication has been created for "{Service Name}"

🔑 Secret Key (keep this safe):
   {BASE32_SECRET}

📱 Current Code: {CODE} (refreshes in {N} seconds)

📲 Scan QR code to import into Authenticator App:
   {otpauth_uri}

💾 Key has been securely saved to: ~/.totp_secrets.json
```

---

## Calling Functions Directly in the Script (Advanced Usage)

If you need to call functions within a Python script:

```python
import sys
sys.path.insert(0, "/path/to/totp/scripts")
from totp_manager import create_new_totp, get_current_code, list_names

# Create new
result = create_new_totp("GitHub", issuer="GitHub")

# Get current code
result = get_current_code("GitHub")
print(result["code"])  # e.g. "847291"
```

---

## Algorithm Notes (RFC 6238 / RFC 4226)

- Hash algorithm: HMAC-SHA1
- Default digits: 6
- Default period: 30 seconds
- Key format: Base32 (uppercase, no spaces)
- Compatible with: Google Authenticator, Authy, 1Password, Microsoft Authenticator, etc.

---

## Important Notes

1. **Time Sync**: TOTP relies on the system clock. If the system time drifts by more than 30 seconds, the code will be invalid.
2. **Key Security**: `~/.totp_secrets.json` stores keys in plaintext. Claude will not expose them to other users.
3. **Backup Reminder**: Remind users to save the `secret` in a secure password manager to prevent loss if their device is lost.
4. **Multiple Accounts**: Use different `name` values for different services to avoid overwriting existing entries.