# 🤖 Discord 机器人配置指南

本指南将帮助你申请 Discord Bot 并获取必要的 Tokens 和 Channel ID。

## 1. 🛠️ 申请 Discord Application & Bot

1.  访问 **[Discord Developer Portal](https://discord.com/developers/applications)** 并登录。
2.  点击右上角的 **"New Application"** 按钮。
3.  输入应用名称（例如 "SecPoster"），勾选同意条款，点击 Create。
4.  在左侧菜单点击 **"Bot"**。
5.  在 "Build-A-Bot" 区域，你可以设置头像和用户名。
6.  **⚠️ 重要**: 在 **"Privileged Gateway Intents"** 区域，勾选 **"Message Content Intent"**。
7.  点击顶部的 **"Reset Token"** 按钮，复制并保存生成的 Token。这是你的 `DISCORD_TOKEN` 🔑。

## 2. 🔗 邀请 Bot 进服务器

1.  在左侧菜单点击 **"OAuth2" -> "URL Generator"**。
2.  在 **SCOPES** 中勾选 `bot`。
3.  **🔑 关键步骤：勾选 BOT PERMISSIONS**
    *   **📝 Text Permissions (文本权限)**:
        *   ✅ `Send Messages`
        *   ✅ `Send Messages in Threads` (**必须勾选**：用于在论坛帖子内回复)
        *   ✅ `Create Public Threads` (**必须勾选**：用于发布新漏洞贴)
        *   ✅ `Attach Files` (用于上传 Markdown/PDF)
        *   ✅ `Embed Links`
        *   ✅ `Read Message History` (建议勾选)
    *   **⚙️ General Permissions (通用权限)**:
        *   ✅ `View Channels` (第一列第4个，**必选**)
4.  复制底部的 Generated URL，在浏览器打开。
5.  选择你要邀请的服务器，授权即可。

## 3. 🆔 获取 Forum Channel ID

1.  打开 Discord 客户端或网页版。
2.  进入你的用户设置 -> **Advanced (高级)** -> 开启 **Developer Mode (开发者模式)** 🛠️。
3.  回到你的服务器，右键点击你想让 Bot 发帖的 **论坛频道 (Forum Channel)**。
4.  点击 **"Copy Channel ID"**。这是你的 `DISCORD_CHANNEL_ID`。

---

## 4. ❓ 常见问题

**Q: 为什么 Bot 发送失败并提示 403 Forbidden?**
A: 请务必检查 Bot 是否在目标频道拥有 `Create Public Threads` 和 `Send Messages in Threads` 权限。某些服务器的身份组设置可能会覆盖 Bot 的默认权限。

**Q: 我找不到某个权限怎么办?**
A: Discord 的权限列表偶尔会更新 UI 布局，建议使用浏览器查找功能 (Ctrl+F) 搜索权限名称。
