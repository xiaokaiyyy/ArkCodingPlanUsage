Volcengine Ark Coding Plan Usage
火山方舟Coding Plan用量监控插件
=====================

<br />

用于 macOS 菜单栏（xbar / SwiftBar）的火山方舟 Coding Plan 用量监控插件，实时显示 API 用量进度，帮助开发者及时了解资源使用情况。

**特性亮点：**
- 实时监控 Coding Plan 用量（小时/周/月三个维度）
- 自动高亮显示用量最高的维度
- 简洁直观的进度条展示
- Cookie 老化预警（7天 ⚠️ / 14天 🔴）
- 从剪贴板一键更新 Cookie，无需手动编辑文件
- 支持 xbar 和 SwiftBar 双平台

## 功能

- **顶部菜单栏** — 自动显示 **小时 / 周 / 月** 三个维度中用量最高的进度条
- **下拉菜单** — 展开查看三个维度的详细用量百分比：
  - 小时用量（5 小时滚动窗口）
  - 周用量（近 7 天）
  - 月度用量（近 30 天）
- **快捷操作** — 下拉菜单底部提供：
  - 从剪贴板更新 Cookie
  - 打开火山方舟控制台

## 前置要求

- macOS
- [xbar](https://xbarapp.com/) 或 [SwiftBar](https://swiftbar.app/)

## 安装

```bash
# 1. 克隆或下载本仓库
git clone https://github.com/xiaokaiyyy/ArkCodingPlanUsage.git
cd ArkCodingPlanUsage

# 2. 复制插件到 xbar 插件目录
cp ark_usage.5m.py ~/Library/Application\ Support/xbar/plugins/

# 3. 确保脚本有执行权限
chmod +x ~/Library/Application\ Support/xbar/plugins/ark_usage.5m.py
```

> 文件名中的 `5m` 表示每 5 分钟自动刷新一次。可修改为 `1m`、`10m`、`30m` 等。

## 配置

插件需要从火山方舟控制台获取 Cookie 才能调用内部 API。

**配置文件保存位置**：`~/.config/ark_config.json`

### 方式一：从剪贴板一键更新（推荐）

1. **登录** [火山方舟控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement)（保持登录状态）。
2. **打开浏览器开发者工具**：`F12` → 切换到 **Network**（网络）标签页。
3. **刷新页面**（`Cmd + R`），在 Network 列表中找到名为 `GetCodingPlanUsage` 的请求。
4. **复制为 cURL**：右键该请求 → `Copy` → `Copy as cURL`。
5. **点击菜单栏** 下拉菜单中的 **"从剪贴板更新 Cookie"**。

插件会自动从剪贴板的 curl 命令中解析 Cookie 和 `x-web-id`，写入配置文件。

### 方式二：手动写入配置文件

```bash
# 创建配置目录
mkdir -p ~/.config

# 手动创建配置文件
cat > ~/.config/ark_config.json << 'EOF'
{
  "cookie": "你的Cookie字符串",
  "web_id": "你的x-web-id值"
}
EOF
```

> `web_id` 可从 curl 命令中 `-H 'x-web-id: ...'` 处获取。

### 刷新插件

- **xbar**：右键菜单栏图标 → Refresh
- **SwiftBar**：右键菜单栏图标 → Refresh All

刷新后，菜单栏应显示当前用量进度条。

## 常见问题

| 问题 | 原因 | 解决 |
| --- | --- | --- |
| 菜单栏显示 "无Cookie" | 配置文件不存在 | 按上文步骤获取 Cookie |
| 显示 "Cookie 过期" | Cookie 已失效 | 重新登录控制台，复制 curl 后点"从剪贴板更新 Cookie" |
| 显示 "API错误: Invalid CSRF token" | Cookie 或 CSRF token 异常 | 重新获取 curl 并更新 |
| 菜单栏标题带 ⚠️ 或 🔴 | Cookie 已超过 7/14 天未更新 | 建议尽快更新 Cookie |
| 显示用量为 0% | 当前周期内无 API 调用 | 正常现象，有调用后自动更新 |

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `ark_usage.5m.py` | xbar / SwiftBar 插件主程序 |
| `README.md` | 本文档 |

## License

MIT License — 详见 [LICENSE](LICENSE) 文件。
