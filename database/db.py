import aiosqlite
import json
from datetime import datetime

DB_PATH = "sweethome.db"

async def init_db():
    """Инициализация базы данных: создание таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                stars_balance INTEGER DEFAULT 0,
                history TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print("[DB] База данных инициализирована")

async def get_or_create_user(user_id: int, username: str = None) -> dict:
    """Получить пользователя или создать нового"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Пробуем получить пользователя
        async with db.execute(
            "SELECT user_id, username, stars_balance, history FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            
            if row:
                return {
                    "user_id": row[0],
                    "username": row[1],
                    "stars_balance": row[2],
                    "history": json.loads(row[3])
                }
            
            # Создаём нового пользователя
            history = json.dumps([])
            await db.execute(
                "INSERT INTO users (user_id, username, stars_balance, history) VALUES (?, ?, 0, ?)",
                (user_id, username, history)
            )
            await db.commit()
            
            print(f"[DB] Создан новый пользователь: {user_id} (@{username})")
            return {
                "user_id": user_id,
                "username": username,
                "stars_balance": 0,
                "history": []
            }

async def update_stars(user_id: int, amount: int):
    """Обновить баланс звёзд пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET stars_balance = stars_balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()
        print(f"[DB] Обновлён баланс пользователя {user_id}: +{amount}")

async def deduct_star(user_id: int) -> bool:
    """Списать 1 звезду. Возвращает True если успешно"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Проверяем баланс
        async with db.execute(
            "SELECT stars_balance FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] < 1:
                return False
        
        # Списываем
        await db.execute(
            "UPDATE users SET stars_balance = stars_balance - 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
        print(f"[DB] Списана 1 звезда у пользователя {user_id}")
        return True

async def add_to_history(user_id: int, role: str, content: str, max_messages: int = 5):
    """Добавить сообщение в историю диалога (храним последние max_messages пар)"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Получаем текущую историю
        async with db.execute(
            "SELECT history FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            history = json.loads(row[0]) if row else []
        
        # Добавляем новое сообщение
        history.append({"role": role, "content": content})
        
        # Ограничиваем длину истории (храним max_messages * 2 — пользователь + бот)
        if len(history) > max_messages * 2:
            history = history[-(max_messages * 2):]
        
        # Сохраняем
        await db.execute(
            "UPDATE users SET history = ? WHERE user_id = ?",
            (json.dumps(history), user_id)
        )
        await db.commit()

async def get_history(user_id: int) -> list:
    """Получить историю диалога"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT history FROM users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else []

async def get_user_count() -> int:
    """Получить количество пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_total_stars() -> int:
    """Получить общий баланс всех звёзд"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT SUM(stars_balance) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] or 0

async def reset_user_balance(user_id: int):
    """Обнулить баланс пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET stars_balance = 0 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()
        print(f"[DB] Обнулён баланс пользователя {user_id}")
