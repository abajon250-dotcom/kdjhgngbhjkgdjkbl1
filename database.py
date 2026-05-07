import sqlite3
from typing import Optional, List, Tuple
from config import DB_NAME

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                access_token TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                phone TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        """)

def save_token(user_id: int, token: str):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO users (user_id, access_token) VALUES (?, ?)", (user_id, token))

def get_token(user_id: int) -> Optional[str]:
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.execute("SELECT access_token FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
    return row[0] if row else None

def revoke_token(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

def get_all_users() -> List[Tuple[int, str]]:
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.execute("SELECT user_id, access_token FROM users")
        return cur.fetchall()

def log_auth(user_id: int, phone: str, status: str):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO auth_logs (user_id, phone, status) VALUES (?, ?, ?)", (user_id, phone, status))