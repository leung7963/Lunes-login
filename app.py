#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import subprocess
import requests
import re
from seleniumbase import SB

# 从环境变量获取账号密码和 TG 配置
EMAIL        = os.environ.get("LUNES_EMAIL") or ""     # 登录邮箱
PASSWORD     = os.environ.get("LUNES_PASSWORD") or ""  # 登录密码
TG_CHAT_ID   = os.environ.get("TG_CHAT_ID") or ""      # chat id,可选
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""    # bot token,可选
TUNNEL_DOMAIN = os.environ.get("TUNNEL_DOMAIN") or ""  # 隧道域名,逗号分隔,可选

LOGIN_URL = "https://betadash.lunes.host/login?next=/"
CTRL_URL  = "https://ctrl.lunes.host"                 # 控制面板基础地址
PROXY_URL = "socks5://127.0.0.1:1081"  # SOCKS5 代理地址

#  Telegram 推送
def send_tg_message(status_icon, status_text, extra_text=""):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("ℹ️ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送。")
        return

    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    if '@' in EMAIL:
        name, domain = EMAIL.split('@', 1)
        if len(name) > 4:
            masked_email = f"{name[:2]}****{name[-2:]}@{domain}"
        else:
            masked_email = f"{name}@{domain}"
    else:
        masked_email = EMAIL[:2] + '****'

    text = (
        f"🇺🇸 Lunes 保活通知\n\n"
        f"{status_icon} {status_text}\n"
        f"👤 登录账户: {masked_email}\n"
        f"⏱️ 登录时间: {current_time_str}"
    )
    if extra_text:
        text += f"\n\n{extra_text}"

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("📩 Telegram 通知发送成功！")
        else:
            print(f"  ⚠️ Telegram 通知发送失败: {r.text}")
    except Exception as e:
        print(f"  ⚠️ Telegram 通知发送异常: {e}")

#  js注入脚本
_EXPAND_JS = """
(function() {
    var ts = document.querySelector('input[name="cf-turnstile-response"]');
    if (!ts) return 'no-turnstile';
    var el = ts;
    for (var i = 0; i < 20; i++) {
        el = el.parentElement;
        if (!el) break;
        var s = window.getComputedStyle(el);
        if (s.overflow === 'hidden' || s.overflowX === 'hidden' || s.overflowY === 'hidden')
            el.style.overflow = 'visible';
        el.style.minWidth = 'max-content';
    }
    document.querySelectorAll('iframe').forEach(function(f){
        if (f.src && f.src.includes('challenges.cloudflare.com')) {
            f.style.width = '300px'; f.style.height = '65px';
            f.style.minWidth = '300px';
            f.style.visibility = 'visible'; f.style.opacity = '1';
        }
    });
    return 'done';
})()
"""

_EXISTS_JS = """
(function(){
    return document.querySelector('input[name="cf-turnstile-response"]') !== null;
})()
"""

_SOLVED_JS = """
(function(){
    var i = document.querySelector('input[name="cf-turnstile-response"]');
    return !!(i && i.value && i.value.length > 20);
})()
"""

_COORDS_JS = """
(function(){
    var iframes = document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {
        var src = iframes[i].src || '';
        if (src.includes('cloudflare') || src.includes('turnstile') || src.includes('challenges')) {
            var r = iframes[i].getBoundingClientRect();
            if (r.width > 0 && r.height > 0)
                return {cx: Math.round(r.x + 30), cy: Math.round(r.y + r.height / 2)};
        }
    }
    var inp = document.querySelector('input[name="cf-turnstile-response"]');
    if (inp) {
        var p = inp.parentElement;
        for (var j = 0; j < 5; j++) {
            if (!p) break;
            var r = p.getBoundingClientRect();
            if (r.width > 100 && r.height > 30)
                return {cx: Math.round(r.x + 30), cy: Math.round(r.y + r.height / 2)};
            p = p.parentElement;
        }
    }
    return null;
})()
"""

_WININFO_JS = """
(function(){
    return {
        sx: window.screenX || 0,
        sy: window.screenY || 0,
        oh: window.outerHeight,
        ih: window.innerHeight
    };
})()
"""

def js_fill_input(sb, selector: str, text: str):
    safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
    sb.execute_script(f"""
    (function(){{
        var el = document.querySelector('{selector}');
        if (!el) return;
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        if (nativeInputValueSetter) {{
            nativeInputValueSetter.call(el, "{safe_text}");
        }} else {{
            el.value = "{safe_text}";
        }}
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }})()
    """)

def _activate_window():
    for cls in ["chrome", "chromium", "Chromium", "Chrome", "google-chrome"]:
        try:
            r = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", cls], capture_output=True, text=True, timeout=3)
            wids = [w for w in r.stdout.strip().split("\n") if w.strip()]
            if wids:
                subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]], timeout=3, stderr=subprocess.DEVNULL)
                time.sleep(0.2)
                return
        except Exception:
            pass
    try:
        subprocess.run(["xdotool", "getactivewindow", "windowactivate"], timeout=3, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def _xdotool_click(x: int, y: int):
    _activate_window()
    try:
        subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], timeout=3, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        subprocess.run(["xdotool", "click", "1"], timeout=2, stderr=subprocess.DEVNULL)
    except Exception:
        os.system(f"xdotool mousemove {x} {y} click 1 2>/dev/null")

def _click_turnstile(sb):
    try:
        coords = sb.execute_script(_COORDS_JS)
    except Exception as e:
        print(f"⚠️ 获取 Turnstile 坐标失败: {e}")
        return
    if not coords:
        print("⚠️ 无法定位 Turnstile 坐标")
        return
    try:
        wi = sb.execute_script(_WININFO_JS)
    except Exception:
        wi = {"sx": 0, "sy": 0, "oh": 800, "ih": 768}
        
    bar = wi["oh"] - wi["ih"]
    ax  = coords["cx"] + wi["sx"]
    ay  = coords["cy"] + wi["sy"] + bar
    print(f"🖱️ 尝试点击 Turnstile ({ax}, {ay})")
    _xdotool_click(ax, ay)

def handle_turnstile(sb) -> bool:
    print("🔍 处理 Cloudflare Turnstile 验证...")
    time.sleep(2)
    
    if sb.execute_script(_SOLVED_JS):
        print("✅ 已静默通过")
        return True

    for _ in range(3):
        try: sb.execute_script(_EXPAND_JS)
        except Exception: pass
        time.sleep(0.5)

    for attempt in range(6):
        if sb.execute_script(_SOLVED_JS):
            print(f"✅ Turnstile 通过（第 {attempt + 1} 次尝试）")
            return True
        try: sb.execute_script(_EXPAND_JS)
        except Exception: pass
        time.sleep(0.3)
        
        _click_turnstile(sb)
        
        for _ in range(8):
            time.sleep(0.5)
            if sb.execute_script(_SOLVED_JS):
                print(f"✅ Turnstile 通过（第 {attempt + 1} 次尝试）")
                return True
        print(f"  ⚠️ 第 {attempt + 1} 次未通过，重试...")

    print("  ❌ Turnstile 6 次均失败")
    return False

def login(sb) -> bool:
    print(f"🌐 打开登录页面(UC+CDP): {LOGIN_URL}")
    sb.activate_cdp_mode(LOGIN_URL)
    time.sleep(6)

    print("⏳ 等待 Cloudflare 验证通过...")
    cf_passed = False
    for i in range(30):
        page_src = sb.get_page_source() or ""
        if 'input[name="email"]' in page_src.lower() or 'name="email"' in page_src.lower():
            cf_passed = True
            print(f"✅ Cloudflare 验证已通过（{i+1}s）")
            break
        time.sleep(1)
    if not cf_passed:
        print("⚠️ Cloudflare 验证可能未通过，继续尝试...")

    try:
        sb.wait_for_element('input[name="email"]', timeout=15)
    except Exception:
        try:
            sb.wait_for_element('input[name="Email"]', timeout=5)
        except Exception:
            print("❌ 页面未加载出登录表单")
            cur_url = sb.get_current_url()
            page_title = sb.get_title() or ""
            print(f"  当前 URL: {cur_url}")
            print(f"  当前标题: {page_title}")
            sb.save_screenshot("login_load_fail.png")
            return False

    print("🍪 关闭可能的 Cookie 弹窗...")
    try:
        for btn in sb.find_elements("button"):
            if "Accept" in (btn.text or ""):
                btn.click()
                time.sleep(0.5)
                break
    except Exception:
        pass

    print(f"📧 填写邮箱...")
    js_fill_input(sb, 'input[name="email"]', EMAIL)
    time.sleep(0.3)
    
    print("🔑 填写密码...")
    js_fill_input(sb, 'input[name="password"]', PASSWORD)
    time.sleep(1)

    if sb.execute_script(_EXISTS_JS):
        if not handle_turnstile(sb):
            print("❌ 登录界面的 Turnstile 验证失败")
            sb.save_screenshot("login_turnstile_fail.png")
            return False
    else:
        print("ℹ️ 未检测到 Turnstile")

    print("🖱️ 点击登录按钮提交登录...")
    sb.click('button[type="submit"]')

    print("⏳ 等待登录跳转...")
    for _ in range(12):
        time.sleep(1)
        cur_url = sb.get_current_url().split('?')[0].lower()
        page_title = sb.get_title() or ""
        if cur_url.startswith("https://betadash.lunes.host") or "Lunes host | Account page" in page_title.lower():
            break

    cur_url = sb.get_current_url().split('?')[0].lower()
    page_title = sb.get_title() or ""
    if "login" not in cur_url and "account" in page_title.lower():
        print(f"✅ 登录成功！(URL: {sb.get_current_url()}, Title: {page_title})")
        return True
        
    print(f"❌ 登录失败，页面未跳转到账户页。(URL: {sb.get_current_url()}, Title: {page_title})")
    sb.save_screenshot("login_failed.png")
    return False

# 访问服务器页面
def visit_server(sb) -> (bool, dict):
    print("🔍 正在查找服务器卡片...")
    try:
        sb.wait_for_element('a.server-card', timeout=15)
    except Exception:
        print("❌ 未找到服务器卡片（可能没有服务器）")
        return False, {"error": "未找到服务器卡片，可能账户无服务器"}

    cards = sb.find_elements('a.server-card')
    if not cards:
        return False, {"error": "未找到服务器卡片"}

    card = cards[0]
    href = card.get_attribute('href')
    if not href:
        return False, {"error": "卡片缺少 href 属性"}

    match = re.search(r'/servers/(\d+)', href)
    if not match:
        return False, {"error": f"无法从 href 解析服务器 ID: {href}"}
    server_id = match.group(1)

    print(f"🖱️ 点击服务器卡片 (ID: {server_id})")
    card.click()
    time.sleep(3)

    expected_url_prefix = f"https://betadash.lunes.host/servers/{server_id}"
    for _ in range(10):
        cur_url = sb.get_current_url().split('?')[0]
        if cur_url == expected_url_prefix:
            break
        time.sleep(1)
    else:
        return False, {"server_id": server_id, "error": f"跳转后 URL 不匹配，当前: {sb.get_current_url()}"}

    page_title = sb.get_title() or ""
    server_name = ""
    if "Server " in page_title:
        server_name = page_title.split("Server ", 1)[-1].strip()
    else:
        server_name = f"ID {server_id}"

    print(f"✅ 成功访问服务器: {server_name} (ID: {server_id})")
    return True, {"server_id": server_id, "server_name": server_name}

# 监控隧道域名状态码
def check_tunnel_status():
    """
    监控隧道域名状态码。
    返回: (异常域名列表, 正常域名列表)
    - 状态码 != 404 视为异常（隧道挂了/重定向/其他错误）
    - 状态码 == 404 视为正常（隧道正常，Cloudflare 404）
    """
    if not TUNNEL_DOMAIN:
        print("ℹ️ 未配置 TUNNEL_DOMAIN，跳过隧道监控。")
        return [], []

    domains = [d.strip() for d in TUNNEL_DOMAIN.split(',') if d.strip()]
    if not domains:
        print("ℹ️ TUNNEL_DOMAIN 为空，跳过隧道监控。")
        return [], []

    abnormal = []
    normal = []
    print(f"🔍 开始监控 {len(domains)} 个隧道域名...")

    for domain in domains:
        # 确保有协议前缀
        url = domain if domain.startswith(('http://', 'https://')) else f"https://{domain}"
        try:
            # 禁用代理，直连检查（隧道域名通常需要直连）
            r = requests.get(url, timeout=10, proxies={"http": None, "https": None}, allow_redirects=True, verify=False)
            status = r.status_code
            print(f"  📡 {domain} -> HTTP {status}")
            if status == 404:
                normal.append(domain)
                print(f"    ✅ 状态码 404，隧道正常，跳过")
            else:
                abnormal.append(domain)
                print(f"    ⚠️ 状态码 {status}，隧道异常，需要重启")
        except requests.exceptions.SSLError:
            # SSL 错误也视为异常（可能证书过期或隧道问题）
            abnormal.append(domain)
            print(f"  📡 {domain} -> SSL 错误，隧道异常，需要重启")
        except Exception as e:
            abnormal.append(domain)
            print(f"  📡 {domain} -> 请求异常: {e}，隧道异常，需要重启")

    return abnormal, normal


# 在控制面板重启服务器
def restart_server_via_ctrl(sb, server_id):
    """
    进入 ctrl.lunes.host/server/{server_id}，点击 start 或 restart 按钮。
    """
    url = f"{CTRL_URL}/server/{server_id}"
    print(f"🔧 打开控制面板: {url}")
    clicked_button = None
    try:
        sb.open(url)
        time.sleep(5)

        # 查找并点击 start / restart 按钮
        clicked = False
        for btn_text in ["restart", "Restart", "RESTART", "start", "Start", "START"]:
            try:
                buttons = sb.find_elements("button")
                for btn in buttons:
                    btn_txt = (btn.text or "").strip()
                    if btn_txt.lower() == btn_text.lower() or btn_text.lower() in btn_txt.lower():
                        print(f"🖱️ 点击按钮: {btn_txt}")
                        btn.click()
                        clicked = True
                        clicked_button = btn_txt
                        time.sleep(3)
                        break
                if clicked:
                    break
            except Exception as e:
                print(f"  ⚠️ 查找 {btn_text} 按钮异常: {e}")

        if not clicked:
            # 尝试用 JS 查找
            try:
                result = sb.execute_script("""
                    (function() {
                        var btns = document.querySelectorAll('button');
                        for (var i = 0; i < btns.length; i++) {
                            var t = (btns[i].innerText || '').trim().toLowerCase();
                            if (t.includes('restart') || t.includes('start')) {
                                btns[i].click();
                                return t;
                            }
                        }
                        return null;
                    })()
                """)
                if result:
                    print(f"🖱️ JS 点击按钮: {result}")
                    clicked = True
                    clicked_button = result
                    time.sleep(3)
            except Exception as e:
                print(f"  ⚠️ JS 查找按钮异常: {e}")

        if not clicked:
            print("  ⚠️ 未找到 start/restart 按钮，页面可能已加载完成或按钮已隐藏")
            return False

        print(f"✅ 已点击 {clicked_button} 按钮")
        print(f"🔁 服务器 {server_id} 已在控制面板执行重启操作")
        return True

    except Exception as e:
        print(f"  ❌ 控制面板操作异常: {e}")
        return False


def main():
    print("#" * 25)
    print("   Lunes 自动登录续期")
    print("#" * 25)

    print(f"🔗 使用 SOCKS5 代理: {PROXY_URL}")

    # 第一步：监控隧道域名状态码
    abnormal, normal = check_tunnel_status()

    with SB(uc=True, headless=False, proxy=PROXY_URL) as sb:
        print("✅ 浏览器已启动")
        try:
            sb.open("https://api.ip.sb/ip")
            print(f"🌐 当前出口真实 IP: {sb.get_text('body')}")
        except Exception:
            pass

        # 进入浏览器会话后登录一次即可复用
        if login(sb):
            # 先检查是否有异常隧道需要重启
            if abnormal:
                print(f"⚠️ 检测到 {len(abnormal)} 个异常隧道域名，需要重启服务器")
                success, info = visit_server(sb)
                if success:
                    server_id = info['server_id']
                    print(f"🔧 服务器 ID: {server_id}")
                    restart_success = restart_server_via_ctrl(sb, server_id)
                    if restart_success:
                        extra = "异常域名:\n" + "\n".join([f"  ⚠️ {d}" for d in abnormal])
                        extra += f"\n服务器: {info['server_name']}\nID: {server_id}"
                        send_tg_message("🔄", "隧道异常已重启", extra)
                    else:
                        extra = "异常域名:\n" + "\n".join([f"  ⚠️ {d}" for d in abnormal])
                        extra += f"\n错误: 控制面板重启失败"
                        send_tg_message("❌", "隧道重启失败", extra)
                else:
                    error_msg = info.get('error', '未知错误')
                    print(f"❌ 访问服务器失败: {error_msg}")
                    extra = "异常域名:\n" + "\n".join([f"  ⚠️ {d}" for d in abnormal])
                    extra += f"\n错误: {error_msg}"
                    send_tg_message("❌", "隧道重启失败", extra)

            # 原有续期逻辑 (访问服务器页面)
            success, info = visit_server(sb)
            if success:
                extra = f"服务器: {info['server_name']}\nID: {info['server_id']}"
                if abnormal:
                    extra += f"\n\n⚠️ 异常隧道已重启: {len(abnormal)} 个"
                send_tg_message("✅", "续期成功", extra)
            else:
                error_msg = info.get('error', '未知错误')
                print(f"❌ 访问服务器失败: {error_msg}")
                extra = f"错误: {error_msg}"
                if 'server_id' in info:
                    extra += f"\n服务器ID: {info['server_id']}"
                send_tg_message("❌", "续期失败", extra)
        else:
            print("\n❌ 登录失败，终止后续续期操作。")
            send_tg_message("❌", "登录失败", "")

if __name__ == "__main__":
    main()
