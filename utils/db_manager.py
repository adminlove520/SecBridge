import sqlite3
import os
import logging
from typing import Optional

class DBManager:
    def __init__(self, db_path="data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 已处理文件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_files (
            file_path TEXT PRIMARY KEY,
            sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent'
        )
        ''')
        
        # 应用状态表 (KV 存储)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        conn.commit()
        conn.close()

    def is_file_processed(self, file_path: str) -> bool:
        """检查文件是否已处理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM processed_files WHERE file_path = ?', (file_path,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_file_processed(self, file_path: str):
        """标记文件为已处理"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR REPLACE INTO processed_files (file_path) VALUES (?)', (file_path,))
            conn.commit()
        except Exception as e:
            logging.error(f"Failed to mark file as processed: {e}")
        finally:
            conn.close()

    def get_state(self, key: str) -> Optional[str]:
        """获取状态值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM app_state WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def set_state(self, key: str, value: str):
        """设置状态值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()
