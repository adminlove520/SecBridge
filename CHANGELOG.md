# 📅 Changelog

## 🔖 [2.1.0] - 2026-01-09

### ✨ Added (新增)
- **🚦 智能队列系统**:
    - 引入平滑限速 (Smart Pacing)，默认每 2 秒发送一个请求。
    - 引入指数退避 (Exponential Backoff)，在遇到网络错误时自动重试。
- **💾 可靠状态管理**:
    - 重构 `main.py` 与 `DiscordPoster` 的交互逻辑。
    - 发送状态更新移至 `on_post_success` 回调，确保只在 Discord 返回 200 OK 后才写入数据库。
- **📚 文档**:
    - 新增 `docs/discord_setup.md`: 详细的图文权限配置指南。
    - 新增 `docs/user_guide.md`: 用户手册。

### 🐛 Fixed (修复)
- **🔍 文件扫描回归**: 修复了使用 `git ls-files` 可能导致的文件扫描不全问题，回退并优化为 `os.walk`。
- **📦 子模块检查**: 增加了对空子模块目录的检测和提示。

## 🔖 [2.0.0] - 2026-01-09

### 🔧 Changed (变更)
- **🗄️ 存储引擎迁移**: 从 JSON 文件 (`state.json`) 迁移至 SQLite (`data.db`)，提高并发稳定性和去重能力。
- **🔄 运行模式**:
    - 新增 `--mode all` (全量扫描模式)。
    - 新增 `--mode incremental` (增量模式 - 默认)。
- **🤖 工作流**: GitHub Actions 增加了 `workflow_dispatch` 输入参数，支持手动触发全量扫描。

### 🗑️ Removed (移除)
- 移除了对 `state.json` 的依赖。

## 🔖 [1.0.0] - Initial Release

- 初始化项目结构。
- 集成 `Vulnerability-Wiki-PoC` 作为 Git 子模块。
- 基础 Markdown/PDF 附件发送功能。
