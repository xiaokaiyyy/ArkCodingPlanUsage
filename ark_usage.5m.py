#!/usr/bin/env python3
# <bitbar.title>Volcengine Ark Usage</bitbar.title>
# <bitbar.author>YourName</bitbar.author>

import json
import os
import ssl
from pathlib import Path
from urllib.request import Request, urlopen

# =============================================================================
# 使用说明：
#   1. 在火山方舟页面按 F12 → Network → 刷新 → 找到 GetCodingPlanUsage
#   2. 右键该请求 → Copy → Copy as cURL
#   3. 把 -b 后面的 Cookie 字符串写入 ~/.config/ark_cookie.txt
#   4. 等 Cookie 过期（通常几天到几周）后，重复步骤 1-3 即可
# =============================================================================

COOKIE_FILE = Path.home() / ".config" / "ark_cookie.txt"
URL = "https://console.volcengine.com/api/top/ark/cn-beijing/2024-01-01/GetCodingPlanUsage?"


def get_cookie():
    if not COOKIE_FILE.exists():
        return None
    return COOKIE_FILE.read_text(encoding="utf-8").strip()


def render_bar(percent, width=5):
    total = width * 2  # 每个半圆代表 10%
    filled = round(percent / 100 * total)
    full = filled // 2
    half = filled % 2
    return "●" * full + ("◐" if half else "") + "○" * (width - full - half)


def get_usage():
    cookie = get_cookie()
    if not cookie:
        print("无 Cookie")
        print("---")
        print("火山方舟 Coding Plan 用量")
        print(f"请在 {COOKIE_FILE} 写入 Cookie")
        return

    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://console.volcengine.com",
            "referer": "https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            ),
            "x-csrf-token": "1185c26b039f8fe284661efd0ddcd1dc",
            "Cookie": cookie,
        }

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = Request(URL, data=b"{}", headers=headers, method="POST")
        with urlopen(req, timeout=10, context=ctx) as response:
            resp = json.loads(response.read().decode("utf-8"))

        quota = resp.get("Result", {}).get("QuotaUsage", [])
        if not quota:
            raise ValueError("未找到用量数据")

        # Build a map of level -> quota record
        quota_map = {q.get("Level", ""): q for q in quota}

        LEVEL_LABELS = {
            "session": "小时用量",
            "weekly": "周用量",
            "monthly": "月度用量",
        }

        # Find the highest usage across all levels for top-level display
        max_quota = max(quota, key=lambda q: q.get("Percent", 0))
        used_percent = max_quota.get("Percent", 0)
        remaining = 100 - used_percent

        bar = render_bar(used_percent)
        print(f"{bar}")
        print("---")
        print("火山方舟 Coding Plan 用量")

        # Render each available quota level in fixed order
        for level in ("session", "weekly", "monthly"):
            record = quota_map.get(level)
            if record is None:
                continue
            pct = record.get("Percent", 0)
            label = LEVEL_LABELS.get(level, level)
            print(f"{label}: {render_bar(pct)} {pct:.1f}%")
    except Exception:
        print("Cookie 过期")
        print("---")
        print("火山方舟 Coding Plan 用量")
        print("Cookie 已失效，请重新获取并写入文件")
        print(f"路径: {COOKIE_FILE}")


if __name__ == "__main__":
    get_usage()
