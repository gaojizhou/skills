---
name: totp
description: >
  管理基于时间的一次性密码（TOTP / 两步验证 / 2FA / MFA）。当用户需要创建、生成、读取、导入或管理 TOTP 验证码时，必须使用此技能。触发场景包括：
  "帮我创建一个两步验证"、"生成 TOTP 密钥"、"我需要 2FA 验证码"、"设置 Google Authenticator"、"生成一次性密码"、"查看我的验证码"、
  以及任何涉及 TOTP / OTP / 两步验证 / 多因素认证（MFA）的请求。即使用户只是说"帮我加个验证"，也应触发此技能。
---

# TOTP 两步验证技能

本技能让 Claude 能够**自主创建、存储、读取 TOTP 密钥**，全程使用 Python 标准库，无需第三方依赖。

---

## 核心脚本

路径：`/mnt/skills/user/totp/scripts/totp_manager.py`（已安装后）
开发/测试时路径：`scripts/totp_manager.py`

**首次使用前**，确认脚本可执行：
```bash
python3 /path/to/totp_manager.py list
```

---

## 存储位置

密钥默认保存在用户主目录：`~/.totp_secrets.json`（权限 600，仅所有者可读）

---

## 标准工作流

### 1. 新建 TOTP 账户（最常见场景）

用户说"帮我创建一个两步验证"时：

```bash
python3 scripts/totp_manager.py create "<账户名>" --issuer "<服务名>"
```

返回 JSON 示例：
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

**向用户展示时必须包含：**
- ✅ 当前 6 位验证码及剩余秒数
- ✅ Base32 密钥（用于导入 Authenticator App）
- ✅ `otpauth://` URI（可用于生成二维码）
- ✅ 存储路径

---

### 2. 获取已保存账户的当前验证码

```bash
python3 scripts/totp_manager.py code "<账户名>"
```

若账户不存在，返回错误提示，引导用户先创建。

---

### 3. 导入已有密钥

用户已有 Base32 密钥（如从其他 Authenticator 迁移）：

```bash
python3 scripts/totp_manager.py import "<账户名>" "<Base32密钥>" --issuer "<服务名>"
```

---

### 4. 列出所有账户

```bash
python3 scripts/totp_manager.py list
```

---

### 5. 删除账户

```bash
python3 scripts/totp_manager.py delete "<账户名>"
```

---

## 在 bash_tool 中调用（Claude 实际使用方式）

Claude 应通过 `bash_tool` 执行上述命令。示例：

```python
# 新建账户
bash_tool(
    command="python3 /mnt/skills/user/totp/scripts/totp_manager.py create 'GitHub' --issuer 'GitHub'",
    description="创建 GitHub TOTP 两步验证密钥"
)

# 获取验证码
bash_tool(
    command="python3 /mnt/skills/user/totp/scripts/totp_manager.py code 'GitHub'",
    description="读取 GitHub 当前 TOTP 验证码"
)
```

---

## 向用户的标准回复格式

创建成功后，Claude 应以清晰格式展示：

```
✅ 已为「{服务名}」创建 TOTP 两步验证

🔑 密钥（请妥善保管）：
   {BASE32_SECRET}

📱 当前验证码：{CODE}（{N} 秒后刷新）

📲 扫描二维码导入 Authenticator App：
   {otpauth_uri}

💾 密钥已加密保存至：~/.totp_secrets.json
```

---

## 直接调用脚本中的函数（高级用法）

如果在 Python 脚本中需要调用：

```python
import sys
sys.path.insert(0, "/path/to/totp/scripts")
from totp_manager import create_new_totp, get_current_code, list_names

# 新建
result = create_new_totp("GitHub", issuer="GitHub")

# 读取当前码
result = get_current_code("GitHub")
print(result["code"])  # e.g. "847291"
```

---

## 算法说明（RFC 6238 / RFC 4226）

- 哈希算法：HMAC-SHA1
- 默认位数：6 位
- 默认周期：30 秒
- 密钥格式：Base32（大写，无空格）
- 兼容：Google Authenticator、Authy、1Password、Microsoft Authenticator 等

---

## 注意事项

1. **时间同步**：TOTP 依赖系统时钟，如系统时间偏差超过 30 秒，验证码将失效
2. **密钥安全**：`~/.totp_secrets.json` 以明文存储密钥，Claude 不会泄露给其他用户
3. **备份提醒**：提醒用户将 `secret` 保存到安全的密码管理器中，防止设备丢失
4. **多账户**：不同服务使用不同 `name`，避免覆盖
