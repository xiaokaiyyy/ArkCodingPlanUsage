#!/usr/bin/env python3
# <bitbar.title>Volcengine Ark Usage</bitbar.title>
# <bitbar.author>YourName</bitbar.author>

import json
import os
import re
import ssl
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CONFIG_FILE = Path.home() / ".config" / "ark_config.json"
URL = "https://console.volcengine.com/api/top/ark/cn-beijing/2024-01-01/GetCodingPlanUsage?"
CONSOLE_URL = "https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&advancedActiveKey=subscribe"

COOKIE_WARN_DAYS = 7
COOKIE_CRIT_DAYS = 14

SCRIPT_PATH = os.path.abspath(__file__)
MENU_UPDATE_COOKIE = f"从剪贴板更新 Cookie | shell={SCRIPT_PATH} param1=update param2=cookie terminal=false refresh=true"


def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def cookie_age_days():
    if not CONFIG_FILE.exists():
        return None
    return (time.time() - os.path.getmtime(CONFIG_FILE)) / 86400


def cookie_age_indicator():
    days = cookie_age_days()
    if days is None:
        return ""
    if days >= COOKIE_CRIT_DAYS:
        return "🔴"
    if days >= COOKIE_WARN_DAYS:
        return "⚠️"
    return ""


def parse_curl_from_clipboard():
    try:
        text = subprocess.check_output(["pbpaste"], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return None, None

    # Parse -b '...' or -b "..."
    cookie = None
    for pat in [r"-b\s+'([^']*)'", r'-b\s+"([^"]*)"', r"--cookie\s+'([^']*)'", r'--cookie\s+"([^"]*)"']:
        m = re.search(pat, text)
        if m:
            cookie = m.group(1).strip()
            break
    if not cookie:
        m = re.search(r"Cookie:\s*(.+)", text, re.IGNORECASE)
        if m:
            cookie = m.group(1).strip()

    # Parse x-web-id header
    web_id = None
    m = re.search(r"-H\s+'x-web-id:\s*([^']+)'", text, re.IGNORECASE)
    if not m:
        m = re.search(r'-H\s+"x-web-id:\s*([^"]+)"', text, re.IGNORECASE)
    if m:
        web_id = m.group(1).strip()

    return cookie, web_id


def update_from_clipboard():
    cookie, web_id = parse_curl_from_clipboard()
    if not cookie:
        return False
    cfg = load_config()
    cfg["cookie"] = cookie
    if web_id:
        cfg["web_id"] = web_id
    save_config(cfg)
    return True


def extract_csrf_token(cookie):
    m = re.search(r"csrfToken=([a-f0-9]+)", cookie)
    return m.group(1) if m else None


def render_bar(percent, width=5):
    total = width * 2
    filled = round(percent / 100 * total)
    full = filled // 2
    half = filled % 2
    return "●" * full + ("◐" if half else "") + "○" * (width - full - half)


def fetch_usage(cookie, web_id=None):
    csrf_token = extract_csrf_token(cookie)
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://console.volcengine.com",
        "referer": CONSOLE_URL,
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        ),
        "Cookie": cookie,
    }
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
    if web_id:
        headers["x-web-id"] = web_id

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = Request(URL, data=b"{}", headers=headers, method="POST")
    with urlopen(req, timeout=10, context=ctx) as response:
        return json.loads(response.read().decode("utf-8"))


def get_usage():
    cfg = load_config()
    cookie = cfg.get("cookie")
    web_id = cfg.get("web_id")
    age_flag = cookie_age_indicator()

    if not cookie:
        print("无Cookie")
        print("---")
        print("火山方舟 Coding Plan 用量")
        print(f"配置文件不存在: {CONFIG_FILE}")
        print(MENU_UPDATE_COOKIE)
        return

    try:
        resp = fetch_usage(cookie, web_id)
    except HTTPError as e:
        label = "Cookie 过期" if e.code in (401, 403) else f"HTTP {e.code}"
        print(f"{label}{age_flag}")
        print("---")
        print("火山方舟 Coding Plan 用量")
        print(f"错误: {label}")
        print(MENU_UPDATE_COOKIE)
        print(f"打开火山控制台 | href={CONSOLE_URL}")
        return
    except (URLError, OSError) as e:
        print(f"网络错误{age_flag}")
        print("---")
        print("火山方舟 Coding Plan 用量")
        print(f"错误: {e}")
        return

    quota = resp.get("Result", {}).get("QuotaUsage", [])
    if not quota:
        err_msg = resp.get("ResponseMetadata", {}).get("Error", {}).get("Message", "未找到用量数据")
        print(f"API错误{age_flag}")
        print("---")
        print("火山方舟 Coding Plan 用量")
        print(f"错误: {err_msg}")
        print(MENU_UPDATE_COOKIE)
        return

    quota_map = {q.get("Level", ""): q for q in quota}

    LEVEL_LABELS = {
        "session": "小时用量",
        "weekly": "周用量",
        "monthly": "月度用量",
    }

    max_quota = max(quota, key=lambda q: q.get("Percent", 0))
    used_percent = max_quota.get("Percent", 0)
    reset_ts = max_quota.get("ResetTimestamp")
    max_label = LEVEL_LABELS.get(max_quota.get("Level", ""), max_quota.get("Level", ""))

    print(f"{used_percent:.0f}%{age_flag}")
    print("---")
    print("火山方舟 Coding Plan 用量")
    if reset_ts:
        now = time.time()
        diff = reset_ts - now
        if diff > 0:
            days = int(diff // 86400)
            hours = int((diff % 86400) // 3600)
            minutes = int((diff % 3600) // 60)
            parts = []
            if days > 0:
                parts.append(f"{days}天")
            if hours > 0 or days > 0:
                parts.append(f"{hours}小时")
            parts.append(f"{minutes}分钟")
            reset_str = "".join(parts)
        else:
            reset_str = "即将刷新"
        print(f"限额（{max_label}）距刷新还剩 {reset_str}")

    for level in ("session", "weekly", "monthly"):
        record = quota_map.get(level)
        if record is None:
            continue
        pct = record.get("Percent", 0)
        label = LEVEL_LABELS.get(level, level)
        print(f"{label}: {render_bar(pct)} {pct:.1f}%")

    print("---")

    days = cookie_age_days()
    if days is not None:
        if days >= COOKIE_CRIT_DAYS:
            print(f"🔴 Cookie 已 {days:.0f} 天未更新，可能即将过期")
        elif days >= COOKIE_WARN_DAYS:
            print(f"⚠️ Cookie 已 {days:.0f} 天未更新")

    print(MENU_UPDATE_COOKIE)
    print(f"打开火山控制台 | href={CONSOLE_URL}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update" and len(sys.argv) > 2 and sys.argv[2] == "cookie":
        if update_from_clipboard():
            print("Cookie 已更新")
        else:
            print("剪贴板中未找到有效 Cookie")
            print("请先在浏览器 F12 → Network → 复制 curl 命令")
        sys.exit(0)

    get_usage()
