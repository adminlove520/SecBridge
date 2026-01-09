import discord
import asyncio
import logging
import os
import time

class DiscordPoster(discord.Client):
    def __init__(self, token, channel_id, config, success_callback=None):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.token = token
        self.target_channel_id = int(channel_id)
        self.queue = asyncio.Queue()
        self.config = config
        self.is_processing = False
        self.ready_event = asyncio.Event()
        self.success_callback = success_callback # 发送成功后的回调函数 (用于更新DB)

        self.retry_delay = config.get('discord', {}).get('retry_delay', 2.0)
        self.max_retries = config.get('discord', {}).get('max_retries', 5)
        self.backoff_factor = config.get('discord', {}).get('retry_backoff', 2.0)

    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.ready_event.set()
        if not self.is_processing:
            self.task = self.loop.create_task(self.process_queue())

    async def process_queue(self):
        self.is_processing = True
        logging.info("启动智能队列处理器...")
        
        while True:
            # 获取任务
            item = await self.queue.get()
            data, attempt = item
            
            try:
                # 强制平滑限速: 确保每次发送之间有最小间隔
                start_time = time.time()
                
                success = await self.send_forum_post(data)
                
                if success:
                    # 发送成功，调用回调更新数据库
                    if self.success_callback:
                        # item['content_path'] 对应的相对路径需要在 main 中处理好传进来，或者这里传完整info
                        # data 中包含 content_path
                        try:
                            # 注意: 回调可能是同步的，如果它是DB操作，通常是同步的。
                            if asyncio.iscoroutinefunction(self.success_callback):
                                await self.success_callback(data)
                            else:
                                self.success_callback(data)
                        except Exception as cb_e:
                            logging.error(f"回调执行失败: {cb_e}")
                else:
                    # 发送失败 (非致命错误，需要重试)
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (self.backoff_factor ** attempt)
                        logging.warning(f"发送失败，将在 {wait_time:.1f}s 后重试 (尝试 {attempt+1}/{self.max_retries})")
                        await asyncio.sleep(wait_time)
                        # 重新入队，增加尝试次数
                        await self.queue.put((data, attempt + 1))
                    else:
                        logging.error(f"达到最大重试次数，丢弃任务: {data['title']}")
                        # 这里可以实现死信队列逻辑，例如写入 failed.log
            
            except Exception as e:
                logging.error(f"严重错误: {e}", exc_info=True)
            
            finally:
                self.queue.task_done()
                
                # 无论成功失败，都执行基础等待，防止在循环中过快消耗空队列
                # 或者是为了平滑流量，我们在成功后也等待
                elapsed = time.time() - start_time
                if elapsed < self.retry_delay:
                    await asyncio.sleep(self.retry_delay - elapsed)

    async def add_to_queue(self, post_data):
        # 存入元组 (数据, 尝试次数)
        await self.queue.put((post_data, 0))
        logging.info(f"已入队: {post_data['title']} (当前队列: {self.queue.qsize()})")

    async def send_forum_post(self, data):
        """
        返回 True 表示发送成功
        返回 False 表示临时错误 (需要重试)
        抛出异常表示严重错误 (或由内部捕获)
        """
        await self.ready_event.wait()
        
        try:
            channel = self.get_channel(self.target_channel_id)
            if not channel:
                channel = await self.fetch_channel(self.target_channel_id)

            if not isinstance(channel, discord.ForumChannel):
                logging.error(f"目标频道 {self.target_channel_id} 类型错误")
                return True # 当作成功处理以避免死循环重试（配置错误重试没用）

            # 标签匹配
            available_tags = channel.available_tags
            applied_tags = []
            for tag_text in data.get('tags', []):
                matching_tag = next((t for t in available_tags if t.name == tag_text), None)
                if matching_tag:
                    applied_tags.append(matching_tag)

            files = []
            for file_path in data.get('attachments', []):
                if os.path.exists(file_path):
                    files.append(discord.File(file_path))
            
            content = f"New PoC Alert!\n\n**{data['title']}**"
            
            logging.info(f"正在发送: {data['title']}")
            
            thread = await channel.create_thread(
                name=data['title'],
                content=content,
                files=files,
                applied_tags=applied_tags
            )
            logging.info(f"✅ 发送成功: {thread.thread.jump_url}")
            return True

        except discord.HTTPException as e:
            if e.status == 429:
                # 429 已经在库层面被处理大部分，如果抛出说明是库放弃了或者虽然sleep了但还是抛错
                # 我们返回 False 让外层队列进行更长时间的避让
                logging.warning(f"触发 HTTP 429: {e}")
                return False
            elif e.status >= 500:
                logging.warning(f"Discord服务端错误 {e.status}: {e}")
                return False
            elif e.status == 400:
                logging.error(f"请求错误 (400)，可能是文件过大或格式错误，不再重试: {e}")
                return True # 视为完成（失败的完成），避免卡死
            else:
                logging.error(f"HTTP异常: {e}")
                return False
        except Exception as e:
            logging.error(f"未知发送错误: {e}")
            return False
        finally:
            # 清理文件句柄
            for f in files:
                f.close()

    async def close_bot(self):
        if not self.queue.empty():
            logging.info("等待队列剩余任务执行...")
            await self.queue.join()
        await self.close()
