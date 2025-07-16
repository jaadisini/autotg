import aiosqlite
import time
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS partners (link TEXT PRIMARY KEY, name TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, username TEXT, action TEXT, timestamp INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS cooldown (chat_id INTEGER PRIMARY KEY, last_used INTEGER)")
        await db.commit()

async def add_partner(link, name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO partners (link, name) VALUES (?, ?)", (link, name))
        await db.commit()

async def del_partner(link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM partners WHERE link = ?", (link,))
        await db.commit()

async def list_partners():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT link, name FROM partners")
        return await cursor.fetchall()

async def check_links_in_partners(text):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT link FROM partners")
        all_links = [row[0] for row in await cursor.fetchall()]
        return [link for link in all_links if link in text]

async def log_action(chat_id, username, action):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO logs (chat_id, username, action, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, username, action, int(time.time()))
        )
        await db.commit()

async def get_recent_logs(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT chat_id, username, action, timestamp FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

async def can_mention(chat_id, cooldown):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT last_used FROM cooldown WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return not row or (int(time.time()) - row[0]) > cooldown

async def update_cooldown(chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO cooldown (chat_id, last_used) VALUES (?, ?)", (chat_id, int(time.time())))
        await db.commit()
