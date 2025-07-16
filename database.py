import aiosqlite
import time
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS partners (link TEXT PRIMARY KEY, name TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS target_groups (chat_id INTEGER PRIMARY KEY)")
        await db.execute("CREATE TABLE IF NOT EXISTS akses_users (user_id INTEGER PRIMARY KEY)")
        await db.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER, action TEXT, timestamp INTEGER)")
        await db.execute("CREATE TABLE IF NOT EXISTS cooldown (group_id INTEGER PRIMARY KEY, last_used INTEGER)")
        await db.commit()

# Partner
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

async def is_partner_link(text):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT link FROM partners")
        all_links = [row[0] for row in await cursor.fetchall()]
        return any(link in text for link in all_links)

# Grup
async def add_group(chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO target_groups (chat_id) VALUES (?)", (chat_id,))
        await db.commit()

async def del_group(chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM target_groups WHERE chat_id = ?", (chat_id,))
        await db.commit()

async def list_groups():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT chat_id FROM target_groups")
        return [row[0] for row in await cursor.fetchall()]

# Akses User
async def grant_akses(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO akses_users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def revoke_akses(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM akses_users WHERE user_id = ?", (user_id,))
        await db.commit()

async def is_user_allowed(user_id):
    if user_id == OWNER_ID:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM akses_users WHERE user_id = ?", (user_id,))
        return bool(await cursor.fetchone())

async def list_akses_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id FROM akses_users")
        return [row[0] for row in await cursor.fetchall()]

# Log dan cooldown
async def log_action(group_id, action):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO logs (group_id, action, timestamp) VALUES (?, ?, ?)", (group_id, action, int(time.time())))
        await db.commit()

async def can_mention(group_id, cooldown):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT last_used FROM cooldown WHERE group_id = ?", (group_id,))
        row = await cursor.fetchone()
        return not row or (int(time.time()) - row[0]) > cooldown

async def update_cooldown(group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO cooldown (group_id, last_used) VALUES (?, ?)", (group_id, int(time.time())))
        await db.commit()
