import sqlite3
import json
import os
import threading

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sweethome.db")
DB_PATH = os.path.normpath(DB_PATH)

_local = threading.local()

def _get_conn():
    """Синхронное соединение для каждого потока"""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn

def _init():
    """Создание таблиц"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            stars_balance INTEGER DEFAULT 0,
            history TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"[DB] Таблицы созданы: {DB_PATH}")

_init()

async def init_db():
    print("[DB] База данных готова")

async def get_or_create_user(user_id: int, username: str = None) -> dict:
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT user_id, username, stars_balance, history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "stars_balance": row[2],
            "history": json.loads(row[3])
        }
    history = json.dumps([])
    conn.execute(
        "INSERT INTO users (user_id, username, stars_balance, history) VALUES (?, ?, 0, ?)",
        (user_id, username, history)
    )
    conn.commit()
    print(f"[DB] Новый пользователь: {user_id} (@{username})")
    return {"user_id": user_id, "username": username, "stars_balance": 0, "history": []}

async def update_stars(user_id: int, amount: int):
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?",
        (amount, user_id)
    )
    conn.commit()
    print(f"[DB] Баланс {user_id}: +{amount}")

async def deduct_star(user_id: int) -> bool:
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT stars_balance FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if not row or row[0] < 1:
        return False
    conn.execute(
        "UPDATE users SET stars_balance = stars_balance - 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    print(f"[DB] Списана 1 звезда у {user_id}")
    return True

async def add_to_history(user_id: int, role: str, content: str, max_messages: int = 5):
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    history = json.loads(row[0]) if row else []
    history.append({"role": role, "content": content})
    if len(history) > max_messages * 2:
        history = history[-(max_messages * 2):]
    conn.execute(
        "UPDATE users SET history = ? WHERE user_id = ?",
        (json.dumps(history), user_id)
    )
    conn.commit()

async def get_history(user_id: int) -> list:
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    return json.loads(row[0]) if row else []

async def get_user_count() -> int:
    conn = _get_conn()
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

async def get_total_stars() -> int:
    conn = _get_conn()
    cursor = conn.execute("SELECT SUM(stars_balance) FROM users")
    row = cursor.fetchone()
    return row[0] or 0

async def reset_user_balance(user_id: int):
    conn = _get_conn()
    conn.execute(
        "UPDATE users SET stars_balance = 0 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()
    print(f"[DB] Баланс {user_id} обнулён")
