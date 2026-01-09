import asyncio
import os
import logging
import yaml
import argparse
import sys
import signal
import json
from typing import Optional

from utils.git_manager import GitManager
from utils.discord_sender import DiscordPoster
from utils.db_manager import DBManager
from scripts.content_formatter import extract_info_from_path
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

async def main():
    parser = argparse.ArgumentParser(description='Discord Vulnerability PoC Poster')
    parser.add_argument('--dry-run', action='store_true', help='不实际发送，只打印日志')
    parser.add_argument('--loop', action='store_true', help='循环运行模式')
    parser.add_argument('--mode', choices=['incremental', 'all'], default='incremental', help='运行模式: 增量(默认) 或 全量扫描')
    args = parser.parse_args()

    load_dotenv()
    config = load_config()

    repo_path = os.path.abspath(config['git']['local_path'])
    
    if not os.path.exists(os.path.join(repo_path, '.git')):
        logging.error(f"子模块路径 {repo_path} 不存在或未初始化。请先运行 'git submodule update --init --recursive'")
        return
    
    # 额外检查：Vulnerability-Wiki-PoC 是否为空（只有.git）
    if not any(f for f in os.listdir(repo_path) if f != '.git'):
        logging.error(f"子模块 {repo_path} 为空！请确保执行了 git submodule update")
        return

    git_manager = GitManager(repo_path)
    db_manager = DBManager()
    
    token = os.getenv(config['discord']['token_env'])
    channel_id = os.getenv(config['discord']['channel_id_env'])
    
    if not token or not channel_id:
        logging.error("未找到 DISCORD_TOKEN 或 DISCORD_CHANNEL_ID 环境变量")
        if not args.dry_run:
            return

    # 回调函数：当 Discord 发送成功后调用
    def on_post_success(data):
        rel_path = os.path.relpath(data['content_path'], repo_path)
        db_manager.mark_file_processed(rel_path)
        logging.info(f"✨ 数据库已更新: {rel_path} 标记为已处理")

    poster = None
    if not args.dry_run:
        # 传入回调函数
        poster = DiscordPoster(token, channel_id, config, success_callback=on_post_success)
        asyncio.create_task(poster.start(token))
        logging.info("等待 Discord Bot 就绪...")
        await poster.ready_event.wait()
    
    # 信号处理，优雅退出
    def signal_handler(sig, frame):
        logging.info("接收到退出信号，正在关闭...")
        if poster:
            asyncio.create_task(poster.close_bot())
        sys.exit(0)
    
    # Windows 下可能不支持某些信号
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception:
        pass

    try:
        while True:
            files_to_process = []
            
            if args.mode == 'all':
                logging.info("开始全量扫描模式...")
                all_md_files = git_manager.get_all_markdown_files()
                logging.info(f"扫描到 {len(all_md_files)} 个 Markdown 文件")
                
                new_files_count = 0
                for file_path in all_md_files:
                    rel_path = os.path.relpath(file_path, repo_path)
                    if not db_manager.is_file_processed(rel_path):
                        files_to_process.append(file_path)
                        new_files_count += 1
                
                logging.info(f"其中 {new_files_count} 个为新文件(未发送过)")

            else: # incremental
                logging.info("开始增量检测模式...")
                old_commit = db_manager.get_state('last_commit')
                current_local_commit = git_manager.repo.head.commit.hexsha

                if not old_commit:
                    logging.info("首次运行增量模式，无历史 Commit 记录。")
                    logging.info("将当前 Commit 标记为基准，不发送历史数据。")
                    db_manager.set_state('last_commit', current_local_commit)
                else:
                    prev_sha, new_sha = git_manager.pull_changes()
                    if prev_sha != new_sha:
                        logging.info(f"检测到更新: {prev_sha[:7]} -> {new_sha[:7]}")
                        changed = git_manager.get_changed_files(prev_sha, new_sha)
                        for f in changed:
                            rel_path = os.path.relpath(f, repo_path)
                            if not db_manager.is_file_processed(rel_path):
                                files_to_process.append(f)
                        
                        db_manager.set_state('last_commit', new_sha)
                    else:
                        logging.info("仓库无新 Commit。")

            # 处理文件队列
            for file_path in files_to_process:
                info = extract_info_from_path(file_path, repo_path)
                
                # 为了日志美观，尝试只显示相对路径的前半部分或标题
                display_path = os.path.relpath(file_path, repo_path)
                logging.info(f"准备入队: {info['title']} (File: {display_path})")
                
                if args.dry_run:
                    # Dry Run 时也只打印相对路径，避免 D:\... 造成的困扰
                    log_info = info.copy()
                    log_info['content_path'] = os.path.relpath(info['content_path'], repo_path)
                    log_info['attachments'] = [os.path.relpath(fp, repo_path) for fp in info['attachments']]
                    logging.info(f"[DRY RUN] 发送内容: {json.dumps(log_info, ensure_ascii=False)}")
                else:
                    await poster.add_to_queue(info)

            if not args.loop:
                if poster and not args.dry_run:
                    logging.info("等待队列任务完成...")
                    await poster.queue.join()
                break
            
            wait_time = config.get('app', {}).get('loop_interval', 300)
            logging.info(f"等待 {wait_time} 秒后进行下一次检查...")
            await asyncio.sleep(wait_time)

    except KeyboardInterrupt:
        logging.info("用户停止程序")
    finally:
        if poster:
            await poster.close_bot()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
