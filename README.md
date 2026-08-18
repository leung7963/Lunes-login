# 🚀 lunes host 自动登录续期（GitHub Actions）

这是一个基于 GitHub Actions 的自动化脚本，用于定时登录自动续期[lunes host](https://betadash.lunes.host/) 应用。

⚠️ 有cf盾,太垃圾的机房节点可能过不了，建议用稍微干净点的节点 [B2proxy住宅代理](https://www.b2proxy.com/signup?code=0F5133)

━━━━━━━━━━━━━━━━━━━━━━

🔐 Secrets 配置说明

Secret 名称 | 是否必填 | 说明  
---|---|---  
LUNES_EMAIL | ✅ 必填 | lunes 登录邮箱  
LUNES_PASSWORD | ✅ 必填 | lunes 登录密码  
NODE_LINK | ❌ 可选 | **节点链接** 或 **订阅链接**（见下方说明）  
TG_BOT_TOKEN | ❌ 可选 | Telegram Bot Token（用于发送通知）  
TG_CHAT_ID | ❌ 可选 | Telegram Chat ID（接收通知的用户或群组 ID）  
  
━━━━━━━━━━━━━━━━━━━━━━

### NODE_LINK 支持两种形式

**1️⃣ 单节点链接**（不配置则直连）

`NODE_LINK` 支持以下任意一种代理协议的完整分享链接：

  * **VLESS** ：`vless://uuid@server:port?security=reality&sni=...&type=ws&...`
  * **VMess** ：`vmess://base64encoded...`
  * **Trojan** ：`trojan://password@server:port?sni=...&type=ws&...`
  * **tuic** ：`tuic://uuid:password@server:port...`
  * **anytls** ：`anytls://uuid@server:port...`
  * **hysteria2** ：`hysteria2://base64@server:port...`
  * **SOCKS5** ：`socks5://user:pass@server:port` 或 `socks://user:pass@server:port`

**2️⃣ 订阅链接**（推荐，自动选可用节点）

`NODE_LINK` 直接填机场订阅链接（`http://` 或 `https://` 开头）即可：

  * 支持 **base64 编码** 和 **明文节点列表** 两种订阅格式
  * 自动下载订阅 → 解码 → 提取所有节点 → **逐个测试连通性**，自动选用第一个可用节点
  * 默认最多尝试前 8 个节点，可通过 workflow 环境变量 `MAX_NODE_TRY` 调整
  * 若某次运行节点全挂，下一次运行会自动重新抓取订阅重试，无需手动更新

> 示例：`NODE_LINK = https://your-sub.example.com/api/v1/client/subscribe?token=xxxx`

### 注意事项

  * 尽量添加一个干净的节点，以免过不了cf盾
  * 订阅模式下脚本会自动跳过失效节点，稳定性更高