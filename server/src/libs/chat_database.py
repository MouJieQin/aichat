import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatDatabase:
    def __init__(self, db_path="chat_history.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
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
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session_time ON messages (session_id, timestamp);"
        )
        self.conn.commit()

    def create_session(self, title: str, ai_config: dict) -> Optional[int]:
        create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (title, create_time, ai_config) VALUES (?, ?, ?)",
            (title, create_time, json.dumps(ai_config)),
        )
        session_id = cursor.lastrowid
        self.conn.commit()
        return session_id

    def delete_session_and_messages(self, session_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self.conn.commit()

    def update_session_title(self, session_id: int, title: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET title = ? WHERE id = ?", (title, session_id)
        )
        self.conn.commit()

    def add_message(
        self, session_id: int, role: str, raw_text: str, parsed_text: str
    ) -> Optional[int]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, raw_text, parsed_text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, raw_text, parsed_text, timestamp),
        )
        message_id = cursor.lastrowid
        self.conn.commit()
        return message_id

    def update_message(self, message_id: int, parsed_text=None, raw_text=None):
        cursor = self.conn.cursor()
        update_fields = []
        params = []
        if raw_text is not None:
            update_fields.append("raw_text = ?")
            params.append(raw_text)
        if parsed_text is not None:
            update_fields.append("parsed_text = ?")
            params.append(parsed_text)
        if not update_fields:
            return
        params.append(message_id)
        query = f"UPDATE messages SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)
        self.conn.commit()

    def delete_message(self, message_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        self.conn.commit()

    def get_session_messages(self, session_id: int, limit=100) -> Optional[list[dict]]:
        cursor = self.conn.cursor()
        if limit == -1:
            cursor.execute(
                "SELECT id, role, raw_text, parsed_text, timestamp FROM messages "
                "WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            )
        else:
            cursor.execute(
                "SELECT id, role, raw_text, parsed_text, timestamp FROM messages "
                "WHERE session_id = ? ORDER BY timestamp LIMIT ?",
                (session_id, limit),
            )
        return cursor.fetchall()

    def get_session_system_messages(self, session_id: int) -> List:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT raw_text FROM messages "
            "WHERE session_id = ? AND role = 'system' ORDER BY timestamp",
            (session_id,),
        )
        return cursor.fetchone()

    def get_session_ai_config(self, session_id: int) -> List:
        cursor = self.conn.cursor()
        cursor.execute("SELECT ai_config FROM sessions WHERE id = ?", (session_id,))
        return cursor.fetchone()

    def update_session_ai_config(self, session_id: int, ai_config: dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET ai_config = ? WHERE id = ?",
            (json.dumps(ai_config), session_id),
        )
        self.conn.commit()

    def get_session(self, session_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return cursor.fetchone()

    def get_all_session_id_title(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title FROM sessions")
        return cursor.fetchall()

    def get_parsed_text(self, message_id: int) -> List:
        cursor = self.conn.cursor()
        cursor.execute("SELECT parsed_text FROM messages WHERE id = ?", (message_id,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()
