from contextlib import closing
import sqlite3
from typing import Dict, List

from pymilvus import Collection


class LocalIDGenerator:
    def __init__(self, collection: Dict[str, Collection], collection_names: List[str]):
        self.collection_names = collection_names
        self.collection = collection
        self.conn = sqlite3.connect(":memory:")  # 内存数据库
        self._init_db()
        self._sync_from_milvus()  # 首次启动同步

    def _init_db(self) -> None:
        with closing(self.conn.cursor()) as cursor:
            # 创建统一计数器表（包含所有集合）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS id_counter (
                    collect_name VARCHAR PRIMARY KEY,
                    current_id INTEGER DEFAULT 0
                )
            """)
            # 初始化所有集合计数器
            for name in self.collection_names:
                cursor.execute("INSERT OR IGNORE INTO id_counter (collect_name, current_id) VALUES (?, 0)", (name,))
            self.conn.commit()

    def _sync_from_milvus(self) -> None:
        with closing(self.conn.cursor()) as cursor:
            for name in self.collection_names:
                count = self.collection[name].num_entities  # 获取所有集合的计数
                cursor.execute("UPDATE id_counter SET current_id = ? WHERE collect_name = ?", (count, name))
            self.conn.commit()

    def get_id(self, collect_name: str) -> int:
        with closing(self.conn.cursor()) as cursor:
            # 原子操作：递增并返回新值
            cursor.execute("SELECT current_id FROM id_counter WHERE collect_name = ?", (collect_name,))
            result = cursor.fetchone()
            self.conn.commit()
            if not result:
                raise ValueError(f"Collection {collect_name} not initialized")
            return result[0]  # type: ignore

    def set_next_id(self, collect_name: str) -> int:
        with closing(self.conn.cursor()) as cursor:
            # 原子操作：递增并返回新值
            cursor.execute("UPDATE id_counter SET current_id = current_id + 1 WHERE collect_name = ? RETURNING current_id", (collect_name,))
            result = cursor.fetchone()
            self.conn.commit()
            if not result:
                raise ValueError(f"Collection {collect_name} not initialized")
            return result[0]  # type: ignore
