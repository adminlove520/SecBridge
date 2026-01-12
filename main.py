import asyncio
import os
import logging
import yaml
import argparse
import re
import sys
import signal
import json
from typing import Optional
from dotenv import load_dotenv

from utils.git_manager import GitManager
from utils.discord_sender import DiscordPoster
from utils.db_manager import DBManager
from utils.reporter import Reporter
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

    db_manager = DBManager()
    
    token = os.getenv(config['discord']['token_env'])
    channel_id = os.getenv(config['discord']['channel_id_env'])
    
    if not token or not channel_id:
        logging.error("未找到 DISCORD_TOKEN 或 DISCORD_CHANNEL_ID 环境变量")
        if not args.dry_run:
            return

    # 回调函数：当 Discord 发送成功后调用
    def on_post_success(data):
        db_path = data.get('db_rel_path')
        if db_path:
            db_manager.mark_file_processed(db_path)
            reporter.record_success()
            logging.info(f"✨ 数据库已更新: {db_path} 标记为已处理")
        else:
            logging.error("回调失败: 数据中缺少 db_rel_path")

    poster = None
    reporter = Reporter(".", db_manager)
    
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
        sources = config.get('sources', [])
        if not sources:
            logging.error("配置文件中未定义任何源 (sources)")
            return

        while True:
            for source in sources:
                source_name = source['name']
                repo_path = os.path.abspath(source['local_path'])
                
                logging.info(f"--- 处理源: {source_name} ---")
                
                if not os.path.exists(os.path.join(repo_path, '.git')):
                    logging.warning(f"跳过 {source_name}: 路径 {repo_path} 不存在或未初始化")
                    continue
                
                # 获取该源对应的 Discord 频道 ID
                source_channel_id = os.getenv(source.get('channel_id_env', ''), channel_id) # 默认使用全局 channel_id
                if not source_channel_id:
                    if args.dry_run:
                        source_channel_id = "123456789" # Dry run 允许使用虚拟 ID
                    else:
                        logging.error(f"源 {source_name} 未定义有效的 DISCORD_CHANNEL_ID")
                        continue

                git_manager = GitManager(repo_path)
                files_to_process = []
                
                # 预定义跳过正则
                skip_patterns = [re.compile(p) for p in source.get('skip_patterns', [])]

                if args.mode == 'all':
                    logging.info(f"[{source_name}] 开始全量扫描...")
                    all_md_files = git_manager.get_all_markdown_files()
                    for file_path in all_md_files:
                        rel_path = os.path.relpath(file_path, repo_path)
                        db_rel_path = f"{source_name}/{rel_path}"
                        
                        # 1. 配置级跳过
                        if any(p.search(rel_path) for p in skip_patterns):
                            logging.debug(f"跳过匹配 skip_patterns 的文件: {rel_path}")
                            continue

                        if not db_manager.is_file_processed(db_rel_path):
                            files_to_process.append(file_path)
                        else:
                            reporter.record_skip()
                else:
                    logging.info(f"[{source_name}] 开始增量检测...")
                    state_key = f"last_commit_{source_name}"
                    old_commit = db_manager.get_state(state_key)
                    current_local_commit = git_manager.repo.head.commit.hexsha

                    if not old_commit:
                        logging.info(f"[{source_name}] 首次运行，标记当前 Commit 为基准")
                        db_manager.set_state(state_key, current_local_commit)
                    else:
                        prev_sha, new_sha = git_manager.pull_changes()
                        if prev_sha != new_sha:
                            logging.info(f"[{source_name}] 检测到更新: {prev_sha[:7]} -> {new_sha[:7]}")
                            changed = git_manager.get_changed_files(prev_sha, new_sha)
                            for f in changed:
                                rel_path = os.path.relpath(f, repo_path)
                                db_rel_path = f"{source_name}/{rel_path}"
                                
                                # 1. 配置级跳过
                                if any(p.search(rel_path) for p in skip_patterns):
                                    continue

                                if not db_manager.is_file_processed(db_rel_path):
                                    files_to_process.append(f)
                                else:
                                    reporter.record_skip()
                            db_manager.set_state(state_key, new_sha)
                        else:
                            logging.info(f"[{source_name}] 无新 Commit")

                # 处理文件队列
                for file_path in files_to_process:
                    db_rel_path = f"{source_name}/{os.path.relpath(file_path, repo_path)}"
                    
                    # 提取信息，包含逻辑校验
                    info = extract_info_from_path(file_path, repo_path, source)
                    
                    # 2. 逻辑级跳过 (如导航文档)
                    if info.get('skip'):
                        logging.info(f"⏭️ 自动跳过导航类文档: {info['title']}")
                        # 标记为已处理，避免下次扫描重复
                        db_manager.mark_file_processed(db_rel_path)
                        continue

                    info['db_rel_path'] = db_rel_path
                    info['target_channel_id'] = int(source_channel_id)
                    
                    logging.info(f"准备入队: {info['title']} (Channel: {source_channel_id}, Tags: {info['tags']})")
                    
                    if args.dry_run:
                        logging.info(f"[DRY RUN] 发送 Preview -> {info['title']} 标签: {info['tags']}")
                        reporter.record_success()
                    else:
                        await poster.add_to_queue(info)

            if not args.loop:
                if poster and not args.dry_run:
                    logging.info("等待所有队列任务完成...")
                    await poster.queue.join()
                
                try:
                    reporter.generate_report()
                except Exception as e:
                    logging.error(f"生成报告失败: {e}")
                break
            
            wait_time = config.get('app', {}).get('loop_interval', 300)
            logging.info(f"等待 {wait_time} 秒后进行下一次全源检查...")
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
