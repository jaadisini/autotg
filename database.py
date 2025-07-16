import aiosqlite
from datetime import datetime

DB_PATH = "partner_groups.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                link TEXT PRIMARY KEY,
                name TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                timestamp TEXT,
                chat_id INTEGER,
                user_id INTEGER,
                detail TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cooldown (
                chat_id INTEGER PRIMARY KEY,
                last_used INTEGER
            )
        """)
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

async def check_links_in_partners(links):
    async with aiosqlite.connect(DB_PATH) as db:
        query = "SELECT link FROM partners WHERE link IN ({})".format(",".join("?" * len(links)))
        cursor = await db.execute(query, links)
        return [row[0] for row in await cursor.fetchall()]

async def insert_log(event, chat_id, user_id, detail):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO logs (event, timestamp, chat_id, user_id, detail) VALUES (?, ?, ?, ?, ?)",
            (event, datetime.now().isoformat(), chat_id, user_id, detail)
        )
        await db.commit()

async def get_logs(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT event, timestamp, chat_id, user_id, detail FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

async def can_mention(chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT last_used FROM cooldown WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        return not row or (datetime.now().timestamp() - row[0]) > 300  # 5 minutes

async def update_cooldown(chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO cooldown (chat_id, last_used) VALUES (?, ?)", (chat_id, int(datetime.now().timestamp())))
        await db.commit()
