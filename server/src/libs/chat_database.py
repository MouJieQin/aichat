import sqlite3
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from libs.log_config import logger


class ChatDatabase:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 使用字典形式返回结果
        self._setup_foreign_keys()
        self._create_tables()

    def _setup_foreign_keys(self) -> None:
        """确保外键约束启用"""
        with self.conn:
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 验证约束是否启用
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            if cursor.fetchone()[0] != 1:
                raise RuntimeError("无法启用外键约束")

    def _create_tables(self) -> None:
        """创建会话和消息表"""
        with self.conn:
            cursor = self.conn.cursor()
            # 创建会话表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    create_time TEXT,
                    ai_config TEXT
                )
            """
            )
            # 创建消息表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    role TEXT,
                    raw_text TEXT,
                    parsed_text TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """
            )
            # 创建索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_session_time ON messages (session_id, timestamp);"
            )

    def create_session(self, title: str, ai_config: dict) -> Optional[int]:
        """创建新会话并返回会话ID"""
        create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (title, create_time, ai_config) VALUES (?, ?, ?)",
                (title, create_time, json.dumps(ai_config, ensure_ascii=False)),
            )
            return cursor.lastrowid

    def delete_session_and_messages(self, session_id: int) -> None:
        """删除会话及其所有消息"""
        with self.conn:
            self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def copy_session(self, session_id: int) -> Optional[int]:
        """复制会话基本信息，不包含消息"""
        with self.conn:
            cursor = self.conn.cursor()
            # 获取源会话信息
            cursor.execute(
                "SELECT title, ai_config FROM sessions WHERE id = ?", (session_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            title, ai_config = row["title"], row["ai_config"]
            create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 创建新会话
            cursor.execute(
                "INSERT INTO sessions (title, create_time, ai_config) VALUES (?, ?, ?)",
                (title, create_time, ai_config),
            )
            return cursor.lastrowid

    def copy_session_system_message(
        self, src_session_id: int, dst_session_id: int
    ) -> None:
        """复制源会话的系统消息到目标会话"""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO messages (session_id, role, raw_text, parsed_text, timestamp) 
                SELECT ?, role, raw_text, parsed_text, timestamp 
                FROM messages 
                WHERE session_id = ? AND role = 'system'
                """,
                (dst_session_id, src_session_id),
            )

    def copy_session_and_messages(self, session_id: int) -> Optional[int]:
        """复制会话及其所有消息"""
        new_session_id = self.copy_session(session_id)
        if new_session_id is None:
            return None

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO messages (session_id, role, raw_text, parsed_text, timestamp) 
                SELECT ?, role, raw_text, parsed_text, timestamp 
                FROM messages 
                WHERE session_id = ?
                """,
                (new_session_id, session_id),
            )
        return new_session_id

    def update_session_title(self, session_id: int, title: str) -> None:
        """更新会话标题"""
        with self.conn:
            self.conn.execute(
                "UPDATE sessions SET title = ? WHERE id = ?", (title, session_id)
            )

    def get_session_title(self, session_id: int) -> Optional[str]:
        """获取会话标题"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return row["title"] if row else None

    def add_message(
        self,
        session_id: int,
        role: str,
        raw_text: str,
        parsed_text: str,
        timestamp: Optional[str] = None,
    ) -> Optional[int]:
        """添加消息到会话"""
        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (session_id, role, raw_text, parsed_text, timestamp) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, role, raw_text, parsed_text, timestamp),
            )
            return cursor.lastrowid

    def update_message(
        self,
        message_id: int,
        parsed_text: Optional[str] = None,
        raw_text: Optional[str] = None,
    ) -> None:
        """更新消息内容"""
        if parsed_text is None and raw_text is None:
            return

        update_fields = []
        params = []

        if raw_text is not None:
            update_fields.append("raw_text = ?")
            params.append(raw_text)

        if parsed_text is not None:
            update_fields.append("parsed_text = ?")
            params.append(parsed_text)

        params.append(message_id)

        query = f"UPDATE messages SET {', '.join(update_fields)} WHERE id = ?"

        with self.conn:
            self.conn.execute(query, params)

    def delete_message(self, message_id: int) -> None:
        """删除消息"""
        with self.conn:
            self.conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))

    def get_session_messages(
        self, session_id: int, limit: int = -1
    ) -> List[Dict[str, Any]]:
        """获取会话的消息列表"""
        cursor = self.conn.cursor()
        query = """
            SELECT id, role, raw_text, parsed_text, timestamp 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY timestamp DESC
        """
        if limit != -1:
            query += " LIMIT ?"
            cursor.execute(query, (session_id, limit))
        else:
            cursor.execute(query, (session_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_session_system_message(self, session_id: int) -> Optional[str]:
        """获取会话的系统消息"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT raw_text 
            FROM messages 
            WHERE session_id = ? AND role = 'system' 
            ORDER BY timestamp
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        return row["raw_text"] if row else None

    def get_session_ai_config(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取会话的AI配置"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT ai_config FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return json.loads(row["ai_config"]) if row else {}

    def update_session_ai_config(self, session_id: int, ai_config: dict) -> None:
        """更新会话的AI配置"""
        with self.conn:
            self.conn.execute(
                "UPDATE sessions SET ai_config = ? WHERE id = ?",
                (json.dumps(ai_config, ensure_ascii=False), session_id),
            )

    def is_session_exist(self, session_id: int) -> bool:
        """检查会话是否存在"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,))
        return cursor.fetchone() is not None

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_session_id_title_config(self) -> List[Dict[str, Any]]:
        """获取所有会话的ID、标题和配置"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, ai_config FROM sessions")
        return [dict(row) for row in cursor.fetchall()]

    def get_parsed_text(self, message_id: int) -> Optional[str]:
        """获取消息的解析文本"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT parsed_text FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        return row["parsed_text"] if row else None

    def close(self) -> None:
        """关闭数据库连接"""
        self.conn.close()


# 数据库操作辅助函数
def get_db_session_count(db: ChatDatabase) -> int:
    """获取数据库中的会话总数"""
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sessions")
    return cursor.fetchone()[0]


def get_db_message_count(db: ChatDatabase) -> int:
    """获取数据库中的消息总数"""
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages")
    return cursor.fetchone()[0]
