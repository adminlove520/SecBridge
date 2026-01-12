# 🛡️ Discord Sec-Bridge (SecPoster)

这是一个高度自动化的安全情报分发机器人，能够监控多个公开漏洞库、技术笔记仓库（如 `Vulnerability-Wiki-PoC`, `Redteam`, `secLinkHub`），并根据内容性质**自动分类**、**智能打标**，将情报精准投递到 Discord 论坛的不同分区。

> **🚀 V3.0 更新 (Pro版)**: 
> - **多源并行监控**: 支持同时订阅无限个 Git 子模块仓库。
> - **论坛分区模型**: 情报自动分发至不同子频道，解决内容堆叠问题。
> - **高级标签引擎**: 支持 Frontmatter (YAML) 解析与正文关键词智能嗅探。
> - **内置 SQLite**: 全量/增量双模式切换，事务级状态保证。

## ✨ 功能特性

- **分区治理 (Forum Partitioning)**: 
    - 📁 **漏洞库区**: 监控 PoC 更新。
    - 🚩 **红队知识区**: 自动同步技术笔记。
    - 🔗 **资源分享区**: 自动链接提取与导航。
- **🏷️ 高级标签引擎**:
    - **Frontmatter 解析**: 识别 Markdown 头部的 `tag: xxx` 标签。
    - **自动分类图标**: 自动附加 🛡️ (PoC), ⚔️ (红蓝), 🚀 (提权) 等动态前缀。
    - **关键词嗅探**: 自动在正文中探测 CVE ID、RCE 等关键技术特征。
- **📁 智能文件管理**:
    - **导航过滤**: 智能识别并跳过 `README.md` 等非干货目录文件。
    - **附件关联**: 自动上传 `.md` 及同目录下的 `.pdf`, `.docx` 报告。
- **🚀 企业级可靠性**:
    - **🚦 智能限速**: 令牌桶控制，平滑流量。
    - **💾 本地 DB**: 采用 SQLite 记录处理状态，确保不丢不重。

## ⚡ 快速开始

### 1. 🛠️ 初始化与同步

```bash
git clone <当前仓库地址>
cd secPoster
pip install -r requirements.txt
git submodule update --init --recursive
```

### 2. ⚙️ 配置环境

复制并配置 `.env.example` 文件（重命名为 `.env`）：

```ini
# Bot 凭据
DISCORD_TOKEN=你的BotToken

# 分区策略 (对应不同的论坛频道 ID)
DISCORD_POC_CHANNEL_ID=漏洞库频道ID
DISCORD_REDTEAM_CHANNEL_ID=红队技术频道ID
DISCORD_WIKI_CHANNEL_ID=资源导航频道ID
```

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
