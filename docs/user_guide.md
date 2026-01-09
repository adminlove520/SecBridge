# 📖 用户使用手册

## ⚡ 快速开始

### 📦 安装依赖

```bash
pip install -r requirements.txt
```

### 🔐 配置环境变量

在项目根目录创建 `.env` 文件（或在系统环境/CI Secrets中设置）：

```ini
DISCORD_TOKEN=你的BotToken
DISCORD_CHANNEL_ID=你的论坛频道ID
```

### 🏃 运行模式

#### 1. 🔄 增量模式 (默认)

仅检测自上次运行以来 Git 仓库的新提交。适合定时任务。

```bash
python main.py
# 等同于
python main.py --mode incremental
```

#### 2. 🏎️ 全量扫描模式

扫描仓库内所有 Markdown 文件，对比数据库中是否已存在。适合初次导入或数据修复。

```bash
# 建议先 Dry Run 看看会发多少
python main.py --mode all --dry-run

# 实际执行
python main.py --mode all
```

#### 3. 🔁 循环监听模式

程序不退出，每隔一段时间（默认 300秒）检查一次。

```bash
python main.py --loop
```

### 🗄️ 数据库

本程序使用 SQLite (`data.db`) 存储已发送的文件记录。
- `processed_files` 表：记录已发送的文件路径。
- `app_state` 表：记录上次 Git Commit hash。

如果需要重置状态，只需删除 `data.db` 即可 🗑️。

### 🛠️ 故障排除

**Q: 遇到 `OSError: [WinError 6] The handle is invalid`?**
A: 这是 Windows 下 Python 进程被外部强制关闭时的常见日志，通常不影响功能。我们已在代码中加入了信号处理来缓解此问题。

**Q: 怎么看日志?**
A: 程序会在控制台输出日志，同时也会写入 `bot.log` 文件 📝。
