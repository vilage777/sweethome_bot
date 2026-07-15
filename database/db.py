import sqlite3
import aiosqlite
import json
import os

# Абсолютный путь — garantнно одна БД
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sweethome.db")
DB_PATH = os.path.normpath(DB_PATH)

def _init_db_sync():
    """Синхронная инициализация таблиц"""
    print(f"[DB] Путь к БД: {DB_PATH}")
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
    # Проверяем что таблица создана
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    result = cursor.fetchone()
    conn.close()
    if result:
        print("[DB] Таблица users создана успешно")
    else:
        print("[DB] ОШИБКА: таблица users не создана!")

# Создаём таблицы при импорте
_init_db_sync()

async def init_db():
    """Асинхронная инициализация"""
    # Дополнительно проверяем при старте бота
    conn = sqlite3.connect(DB_PATH)
    conn.execute("SELECT COUNT(*) FROM users")
    conn.close()
    print("[DB] База данных проверена")

async def _run(sql, params=None):
    """Выполнить SQL-запрос"""
    db = await aiosqlite.connect(DB_PATH)
    try:
        if params:
            cursor = await db.execute(sql, params)
        else:
            cursor = await db.execute(sql)
        result = await cursor.fetchall()
        await db.commit()
        return result
    finally:
        await db.close()

async def get_or_create_user(user_id: int, username: str = None) -> dict:
    """Получить пользователя или создать нового"""
    rows = await _run(
        "SELECT user_id, username, stars_balance, history FROM users WHERE user_id = ?",
        (user_id,)
    )
    if rows:
        row = rows[0]
        return {
            "user_id": row[0],
            "username": row[1],
            "stars_balance": row[2],
            "history": json.loads(row[3])
        }

    history = json.dumps([])
    await _run(
        "INSERT INTO users (user_id, username, stars_balance, history) VALUES (?, ?, 0, ?)",
        (user_id, username, history)
    )
    print(f"[DB] Новый пользователь: {user_id} (@{username})")
    return {"user_id": user_id, "username": username, "stars_balance": 0, "history": []}

async def update_stars(user_id: int, amount: int):
    """Обновить баланс звёзд"""
    await _run(
        "UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?",
        (amount, user_id)
    )
    print(f"[DB] Баланс {user_id}: +{amount}")

async def deduct_star(user_id: int) -> bool:
    """Списать 1 звезду"""
    rows = await _run(
        "SELECT stars_balance FROM users WHERE user_id = ?",
        (user_id,)
    )
    if not rows or rows[0][0] < 1:
        return False
    await _run(
        "UPDATE users SET stars_balance = stars_balance - 1 WHERE user_id = ?",
        (user_id,)
    )
    print(f"[DB] Списана 1 звезда у {user_id}")
    return True

async def add_to_history(user_id: int, role: str, content: str, max_messages: int = 5):
    """Добавить сообщение в историю"""
    rows = await _run(
        "SELECT history FROM users WHERE user_id = ?",
        (user_id,)
    )
    history = json.loads(rows[0][0]) if rows else []
    history.append({"role": role, "content": content})
    if len(history) > max_messages * 2:
        history = history[-(max_messages * 2):]
    await _run(
        "UPDATE users SET history = ? WHERE user_id = ?",
        (json.dumps(history), user_id)
    )

async def get_history(user_id: int) -> list:
    """Получить историю диалога"""
    rows = await _run(
        "SELECT history FROM users WHERE user_id = ?",
        (user_id,)
    )
    return json.loads(rows[0][0]) if rows else []

async def get_user_count() -> int:
    """Количество пользователей"""
    rows = await _run("SELECT COUNT(*) FROM users")
    return rows[0][0]

async def get_total_stars() -> int:
    """Общий баланс звёзд"""
    rows = await _run("SELECT SUM(stars_balance) FROM users")
    return rows[0][0] or 0

async def reset_user_balance(user_id: int):
    """Обнулить баланс"""
    await _run(
        "UPDATE users SET stars_balance = 0 WHERE user_id = ?",
        (user_id,)
    )
    print(f"[DB] Баланс {user_id} обнулён")
