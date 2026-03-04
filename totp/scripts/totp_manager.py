#!/usr/bin/env python3
"""
TOTP Manager - Time-based One-Time Password (RFC 6238) Management Tool
Implemented using Python standard library, no third-party dependencies required
Storage location: ~/.totp_secrets.json
"""

import hmac
import hashlib
import struct
import time
import base64
import os
import json
import sys
import argparse
import secrets
import string


# ─── STORAGE PATH ───────────────────────────────────────────
STORAGE_PATH = os.path.expanduser("~/.totp_secrets.json")


# ─── TOTP CORE ALGORITHM (RFC 6238 / RFC 4226) ────────────────
def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    """Calculate HOTP value"""
    try:
        key = base64.b32decode(secret_b32.upper().replace(" ", ""), casefold=True)
    except Exception as e:
        raise ValueError(f"Base32 key decoding failed: {e}")
    
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def generate_totp(secret_b32: str, digits: int = 6, period: int = 30) -> str:
    """Generate the current TOTP code"""
    counter = int(time.time()) // period
    return _hotp(secret_b32, counter, digits)


def totp_remaining_seconds(period: int = 30) -> int:
    """Return the remaining valid seconds for the current TOTP code"""
    return period - (int(time.time()) % period)


def generate_secret(length: int = 20) -> str:
    """Generate a random Base32 secret key (160 bits, per RFC 4226 recommendation)"""
    alphabet = string.ascii_uppercase + "234567"  # Base32 character set
    raw = secrets.token_bytes(length)
    # Encode random bytes as Base32
    secret = base64.b32encode(raw).decode("utf-8")
    return secret


def build_otpauth_uri(account: str, secret: str, issuer: str = "",
                      digits: int = 6, period: int = 30) -> str:
    """Generate an otpauth:// URI (can be used for QR codes)"""
    label = f"{issuer}:{account}" if issuer else account
    uri = f"otpauth://totp/{label}?secret={secret}&digits={digits}&period={period}"
    if issuer:
        uri += f"&issuer={issuer}"
    return uri


# ─── LOCAL STORAGE ────────────────────────────────────────────
def _load_store() -> dict:
    if not os.path.exists(STORAGE_PATH):
        return {}
    with open(STORAGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(data: dict):
    os.makedirs(os.path.dirname(STORAGE_PATH) if os.path.dirname(STORAGE_PATH) else ".", exist_ok=True)
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.chmod(STORAGE_PATH, 0o600)  # Owner read/write only


def save_secret(name: str, secret: str, issuer: str = "",
                digits: int = 6, period: int = 30) -> dict:
    """Save a TOTP entry"""
    store = _load_store()
    entry = {
        "secret": secret,
        "issuer": issuer,
        "digits": digits,
        "period": period,
        "created_at": int(time.time()),
    }
    store[name] = entry
    _save_store(store)
    return entry


def get_secret(name: str) -> dict | None:
    """Read a TOTP entry"""
    store = _load_store()
    return store.get(name)


def list_names() -> list[str]:
    """List all saved entry names"""
    return list(_load_store().keys())


def delete_secret(name: str) -> bool:
    """Delete a TOTP entry"""
    store = _load_store()
    if name not in store:
        return False
    del store[name]
    _save_store(store)
    return True


# ─── HIGH-LEVEL OPERATIONS (for Claude to call) ──────────────────────────
def create_new_totp(name: str, issuer: str = "",
                    digits: int = 6, period: int = 30) -> dict:
    """
    Create a brand new TOTP account:
    - Generate a random secret key
    - Save to local storage
    - Return complete information
    """
    secret = generate_secret()
    save_secret(name, secret, issuer=issuer, digits=digits, period=period)
    uri = build_otpauth_uri(name, secret, issuer=issuer, digits=digits, period=period)
    code = generate_totp(secret, digits=digits, period=period)
    remaining = totp_remaining_seconds(period=period)
    return {
        "name": name,
        "secret": secret,
        "issuer": issuer,
        "digits": digits,
        "period": period,
        "otpauth_uri": uri,
        "current_code": code,
        "remaining_seconds": remaining,
        "storage_path": STORAGE_PATH,
    }


def get_current_code(name: str) -> dict | None:
    """
    Read a saved entry and return the current TOTP code
    """
    entry = get_secret(name)
    if not entry:
        return None
    code = generate_totp(entry["secret"], digits=entry["digits"], period=entry["period"])
    remaining = totp_remaining_seconds(period=entry["period"])
    return {
        "name": name,
        "code": code,
        "remaining_seconds": remaining,
        "issuer": entry.get("issuer", ""),
    }


# ─── CLI ENTRY POINT ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="TOTP Secret Key Management Tool")
    sub = parser.add_subparsers(dest="cmd")

    # create
    p_create = sub.add_parser("create", help="Create a new TOTP account")
    p_create.add_argument("name", help="Account name")
    p_create.add_argument("--issuer", default="", help="Issuer (optional)")
    p_create.add_argument("--digits", type=int, default=6)
    p_create.add_argument("--period", type=int, default=30)

    # code
    p_code = sub.add_parser("code", help="Get the current TOTP verification code")
    p_code.add_argument("name", help="Account name")

    # list
    sub.add_parser("list", help="List all accounts")

    # delete
    p_del = sub.add_parser("delete", help="Delete an account")
    p_del.add_argument("name")

    # import
    p_imp = sub.add_parser("import", help="Import an existing secret key")
    p_imp.add_argument("name")
    p_imp.add_argument("secret", help="Base32 secret key")
    p_imp.add_argument("--issuer", default="")
    p_imp.add_argument("--digits", type=int, default=6)
    p_imp.add_argument("--period", type=int, default=30)

    args = parser.parse_args()

    if args.cmd == "create":
        result = create_new_totp(args.name, issuer=args.issuer,
                                  digits=args.digits, period=args.period)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "code":
        result = get_current_code(args.name)
        if result is None:
            print(json.dumps({"error": f"Account not found: {args.name}"}))
            sys.exit(1)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "list":
        names = list_names()
        print(json.dumps({"accounts": names}, ensure_ascii=False, indent=2))

    elif args.cmd == "delete":
        ok = delete_secret(args.name)
        print(json.dumps({"deleted": ok, "name": args.name}))

    elif args.cmd == "import":
        save_secret(args.name, args.secret, issuer=args.issuer,
                    digits=args.digits, period=args.period)
        code = generate_totp(args.secret, digits=args.digits, period=args.period)
        print(json.dumps({
            "name": args.name,
            "imported": True,
            "current_code": code,
            "remaining_seconds": totp_remaining_seconds(args.period),
        }, ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()