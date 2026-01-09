# 🛡️ Discord Vulnerability PoC Poster

这是一个自动化机器人，用于监控漏洞 PoC 仓库并将最新的漏洞情报发布到 Discord 论坛频道。

> **🚀 V2.0 更新**: 全面升级为 SQLite 存储，支持全量/增量扫描模式，并内置了企业级的智能限速队列系统。

## ✨ 功能特性

- **🔍 智能监控**:
    - **🔄 增量模式**: 基于 Git Commit 哈希检测变更，高效低耗。
    - **🏎️ 全量模式**: 支持扫描整个仓库，自动通过数据库去重，适合数据修复或初次导入。
- **💾 可靠存储**:
    - 使用 **🗄️ SQLite** 本地数据库记录发送状态，拒绝“假发”或重复发送。
    - ✅ 事务级状态管理：只有 Discord API 返回成功后才标记已处理。
- **🛡️ 稳健投递**:
    - **🚦 智能限速**: 令牌桶算法控制发送频率（平滑流量，防 429）。
    - **↩️ 指数退避**: 网络波动时自动按 `2s -> 4s -> 8s` 策略重试。
- **📝 自动排版**:
    - 🏷️ 自动提取年份标签 (e.g., `2025`)。
    - 📰 智能生成规范标题 (`年份-漏洞名称`)。
    - 📎 自动上传 `.md` 内容及同目录下的 `.pdf` 报告。

## ⚡ 快速开始

### 1. 🛠️ 环境准备

```bash
git clone <当前仓库地址>
cd secPoster
pip install -r requirements.txt
```

### 2. 🔗 初始化子模块

```bash
git submodule init
git submodule update
```

### 3. ⚙️ 配置

复制或创建 `.env` 文件（或直接设置环境变量）：

```ini
DISCORD_TOKEN=你的BotToken
DISCORD_CHANNEL_ID=你的论坛频道ID
```
*更多配置项（如重试间隔）可在 `config.yaml` 中调整。*

### 4. ▶️ 运行

#### 🔄 增量监控 (推荐用于日常)
仅检查有变动的 Commit。
```bash
python main.py
# 或
python main.py --mode incremental
```

#### 🏎️ 全量扫描 (推荐用于初次)
扫描所有文件，数据库会自动过滤已发送的。
```bash
python main.py --mode all
```

#### 🔁 循环监听
```bash
python main.py --loop
```

#### 🧪 测试运行 (Dry Run)
只打印日志，不发请求，不写数据库。
```bash
python main.py --dry-run --mode all
```

## 📂 目录结构

- `utils/`: 🔧 核心组件 (Git 管理, SQLite 封装, 智能发送队列)
- `scripts/`: 📜 业务脚本 (内容提取与格式化)
- `docs/`: 📚 详细文档 (Discord 申请指南, 用户手册)
- `data.db`: 🗄️ SQLite 数据库 (自动生成)
- `Vulnerability-Wiki-PoC/`: 📦 漏洞数据源

## 📚 文档资源

- [🤖 Discord 机器人申请与权限配置指南](docs/discord_setup.md)
- [📖 详细用户手册](docs/user_guide.md)

## 📅 更新日志

查看 [CHANGELOG.md](CHANGELOG.md)
