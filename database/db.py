import aiosqlite
import json

DB_PATH = "sweethome.db"
_db = None

async def get_db():
    """Получить единственное соединение с БД"""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                stars_balance INTEGER DEFAULT 0,
                history TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await _db.commit()
        print("[DB] База данных инициализирована")
    return _db

async def init_db():
    """Инициализация базы данных"""
    await get_db()

async def get_or_create_user(user_id: int, username: str = None) -> dict:
    """Получить пользователя или создать нового"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT user_id, username, stars_balance, history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "stars_balance": row[2],
            "history": json.loads(row[3])
        }

    history = json.dumps([])
    await db.execute(
        "INSERT INTO users (user_id, username, stars_balance, history) VALUES (?, ?, 0, ?)",
        (user_id, username, history)
    )
    await db.commit()
    print(f"[DB] Создан новый пользователь: {user_id} (@{username})")
    return {"user_id": user_id, "username": username, "stars_balance": 0, "history": []}

async def update_stars(user_id: int, amount: int):
    """Обновить баланс звёзд"""
    db = await get_db()
    await db.execute(
        "UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?",
        (amount, user_id)
    )
    await db.commit()
    print(f"[DB] Баланс пользователя {user_id}: +{amount}")

async def deduct_star(user_id: int) -> bool:
    """Списать 1 звезду"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT stars_balance FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row or row[0] < 1:
        return False
    await db.execute(
        "UPDATE users SET stars_balance = stars_balance - 1 WHERE user_id = ?",
        (user_id,)
    )
    await db.commit()
    print(f"[DB] Списана 1 звезда у {user_id}")
    return True

async def add_to_history(user_id: int, role: str, content: str, max_messages: int = 5):
    """Добавить сообщение в историю"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    history = json.loads(row[0]) if row else []

    history.append({"role": role, "content": content})
    if len(history) > max_messages * 2:
        history = history[-(max_messages * 2):]

    await db.execute(
        "UPDATE users SET history = ? WHERE user_id = ?",
        (json.dumps(history), user_id)
    )
    await db.commit()

async def get_history(user_id: int) -> list:
    """Получить историю диалога"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT history FROM users WHERE user_id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    await cursor.close()
    return json.loads(row[0]) if row else []

async def get_user_count() -> int:
    """Количество пользователей"""
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    row = await cursor.fetchone()
    await cursor.close()
    return row[0]

async def get_total_stars() -> int:
    """Общий баланс звёзд"""
    db = await get_db()
    cursor = await db.execute("SELECT SUM(stars_balance) FROM users")
    row = await cursor.fetchone()
    await cursor.close()
    return row[0] or 0

async def reset_user_balance(user_id: int):
    """Обнулить баланс"""
    db = await get_db()
    await db.execute(
        "UPDATE users SET stars_balance = 0 WHERE user_id = ?",
        (user_id,)
    )
    await db.commit()
    print(f"[DB] Баланс {user_id} обнулён")
