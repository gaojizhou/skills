#!/usr/bin/env python3
"""
TOTP Manager - 基于时间的一次性密码(RFC 6238)管理工具
使用 Python 标准库实现，无需第三方依赖
存储位置: ~/.totp_secrets.json
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


# ─── 存储路径 ───────────────────────────────────────────
STORAGE_PATH = os.path.expanduser("~/.totp_secrets.json")


# ─── TOTP 核心算法 (RFC 6238 / RFC 4226) ────────────────
def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    """计算 HOTP 值"""
    try:
        key = base64.b32decode(secret_b32.upper().replace(" ", ""), casefold=True)
    except Exception as e:
        raise ValueError(f"Base32 密钥解码失败: {e}")
    
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10 ** digits)).zfill(digits)


def generate_totp(secret_b32: str, digits: int = 6, period: int = 30) -> str:
    """生成当前 TOTP 码"""
    counter = int(time.time()) // period
    return _hotp(secret_b32, counter, digits)


def totp_remaining_seconds(period: int = 30) -> int:
    """返回当前 TOTP 码剩余有效秒数"""
    return period - (int(time.time()) % period)


def generate_secret(length: int = 20) -> str:
    """生成随机 Base32 密钥（160 bits，符合 RFC 4226 推荐）"""
    alphabet = string.ascii_uppercase + "234567"  # Base32 字符集
    raw = secrets.token_bytes(length)
    # 将随机字节编码为 Base32
    secret = base64.b32encode(raw).decode("utf-8")
    return secret


def build_otpauth_uri(account: str, secret: str, issuer: str = "",
                      digits: int = 6, period: int = 30) -> str:
    """生成 otpauth:// URI（可用于二维码）"""
    label = f"{issuer}:{account}" if issuer else account
    uri = f"otpauth://totp/{label}?secret={secret}&digits={digits}&period={period}"
    if issuer:
        uri += f"&issuer={issuer}"
    return uri


# ─── 本地存储 ────────────────────────────────────────────
def _load_store() -> dict:
    if not os.path.exists(STORAGE_PATH):
        return {}
    with open(STORAGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(data: dict):
    os.makedirs(os.path.dirname(STORAGE_PATH) if os.path.dirname(STORAGE_PATH) else ".", exist_ok=True)
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.chmod(STORAGE_PATH, 0o600)  # 仅所有者可读写


def save_secret(name: str, secret: str, issuer: str = "",
                digits: int = 6, period: int = 30) -> dict:
    """保存一个 TOTP 条目"""
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
    """读取一个 TOTP 条目"""
    store = _load_store()
    return store.get(name)


def list_names() -> list[str]:
    """列出所有已保存的条目名称"""
    return list(_load_store().keys())


def delete_secret(name: str) -> bool:
    """删除一个 TOTP 条目"""
    store = _load_store()
    if name not in store:
        return False
    del store[name]
    _save_store(store)
    return True


# ─── 高层操作（供 Claude 调用）──────────────────────────
def create_new_totp(name: str, issuer: str = "",
                    digits: int = 6, period: int = 30) -> dict:
    """
    创建一个全新的 TOTP 账户：
    - 生成随机密钥
    - 保存到本地
    - 返回完整信息
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
    读取已保存条目并返回当前 TOTP 码
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


# ─── CLI 入口 ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="TOTP 密钥管理工具")
    sub = parser.add_subparsers(dest="cmd")

    # create
    p_create = sub.add_parser("create", help="新建 TOTP 账户")
    p_create.add_argument("name", help="账户名称")
    p_create.add_argument("--issuer", default="", help="发行方（可选）")
    p_create.add_argument("--digits", type=int, default=6)
    p_create.add_argument("--period", type=int, default=30)

    # code
    p_code = sub.add_parser("code", help="获取当前 TOTP 验证码")
    p_code.add_argument("name", help="账户名称")

    # list
    sub.add_parser("list", help="列出所有账户")

    # delete
    p_del = sub.add_parser("delete", help="删除账户")
    p_del.add_argument("name")

    # import
    p_imp = sub.add_parser("import", help="导入已有密钥")
    p_imp.add_argument("name")
    p_imp.add_argument("secret", help="Base32 密钥")
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
            print(json.dumps({"error": f"未找到账户: {args.name}"}))
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
