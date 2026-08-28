## 🚀 lunes host 自动登录续期（GitHub Actions）

这是一个基于 GitHub Actions 的自动化脚本，用于定时登录自动续期[lunes host](https://betadash.lunes.host/) 应用。

⚠️ 有cf盾,太垃圾的机房节点可能过不了，建议用稍微干净点的节点 [B2proxy住宅代理](https://www.b2proxy.com/signup?code=0F5133)

---

## 🔐 Secrets 配置说明

|| Secret 名称         | 是否必填 | 说明                                              |
||--------------------- |----------|---------------------------------------------------|
|| LUNES_EMAIL     | ✅ 必填  | lunes 登录邮箱                                    |
|| LUNES_PASSWORD  | ✅ 必填  | lunes 登录密码                                    |
|| NODE_LINK       | ❌ 可选  | 代理链接或订阅，如 vless:// ss:// vmess:// trojan:// ... 或 https://sub.example.com/token |
|| TG_BOT_TOKEN    | ❌ 可选  | Telegram Bot Token（用于发送通知）                     |
|| TG_CHAT_ID      | ❌ 可选  | Telegram Chat ID（接收通知的用户或群组 ID）              |
|| TUNNEL_DOMAIN   | ❌ 可选  | 隧道域名（逗号分隔），如 `lunes.0662.ip-ddns.com`。脚本会自动检查状态码，404=正常跳过，非404=自动重启服务器 |

---

## 🌐 隧道监控功能

- 脚本会检查 `TUNNEL_DOMAIN` 环境变量配置的隧道域名状态码
- ✅ 状态码 `404` → 隧道正常，跳过
- ⚠️ 状态码非 `404`（200/302/502/超时等） → 隧道异常，自动登录并进入控制面板点击 **start/restart**
- 每次运行时自动执行，无需额外配置

---

### 代理格式（确认在v2rayN里使用正常的节点）

`NODE_LINK` 支持以下任意一种代理协议的完整分享链接（不配置则直连）：
- **VLESS**：`vless://uuid@server:port?security=reality&sni=...&type=ws&...`
- **VMess**：`vmess://base64encoded...`
- **ShadowSocks**：`ss://method:password@server:port` 或 `ss://base64(server:password)@server:port`
- **Trojan**：`trojan://password@server:port?sni=...&type=ws&...`
- **tuic**：`tuic://uuid:password@server:port...`
- **anytls**：`anytls://uuid@server:port...`
- **hysteria2**：`hysteria2://base64@server:port...`
- **SOCKS5**：`socks5://user:pass@server:port` 或 `socks://user:pass@server:port`

### 订阅链接（`http://` / `https://`）：

- 支持 **Clash YAML**、**base64 编码**、**明文节点列表** 三种订阅格式
- 自动下载 → 解析 → 逐个测试 → 使用第一个可用节点
- 默认最多尝试 8 个节点（可通过 `MAX_NODE_TRY` 环境变量调整）

### 注意事项
- 尽量添加一个干净的节点，以免过不了cf盾