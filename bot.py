import asyncio
import re
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
import config

DB_PATH = "partner_groups.db"

# Bot client
app = Client("tagall_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

# Inisialisasi database
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
                chat_id INTEGER,
                username TEXT,
                action TEXT,
                timestamp INTEGER
            )
        """)
        await db.commit()

# Database helpers
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
        query = "SELECT link FROM partners WHERE link IN ({})".format(",".join(["?"] * len(links)))
        cursor = await db.execute(query, links)
        return [row[0] for row in await cursor.fetchall()]

async def log_action(chat_id, username, action):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO logs (chat_id, username, action, timestamp) VALUES (?, ?, ?, ?)",
                         (chat_id, username, action, int(time.time())))
        await db.commit()

async def get_recent_logs(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT chat_id, username, action, timestamp FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        return await cursor.fetchall()

last_mention_time = {}
MENTION_COOLDOWN = 300  # 5 menit

# Commands
@app.on_message(filters.command("start"))
async def cmd_start(_, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Menu Bantuan", callback_data="help_menu")]
    ])
    await message.reply(
        "🤖 Selamat datang di Bot TagAll Otomatis!\nGunakan menu di bawah untuk bantuan.",
        reply_markup=keyboard
    )

@app.on_message(filters.command("help"))
async def cmd_help(_, message: Message):
    help_text = (
        "<b>📋 Menu Bantuan:</b>\n\n"
        "/addpartner <link_group> <nama_group> - Tambah partner group\n"
        "/delpartner <link_group> - Hapus partner group\n"
        "/listpartner - Lihat daftar partner\n"
        "/logview - Lihat log aktivitas\n"
        "/help - Tampilkan menu bantuan"
    )
    await message.reply(help_text)

@app.on_callback_query(filters.regex("^help_menu$"))
async def help_callback(_, callback_query):
    help_text = (
        "<b>📋 Menu Bantuan:</b>\n\n"
        "/addpartner <link_group> <nama_group> - Tambah partner group\n"
        "/delpartner <link_group> - Hapus partner group\n"
        "/listpartner - Lihat daftar partner\n"
        "/logview - Lihat log aktivitas\n"
        "/help - Tampilkan menu bantuan"
    )
    await callback_query.message.edit_text(help_text)

@app.on_message(filters.command("addpartner") & filters.group)
async def cmd_addpartner(_, message: Message):
    if len(message.command) < 3:
        return await message.reply("❌ Format salah. Gunakan:\n`/addpartner <link_group> <nama_group>`", quote=True)
    link = message.command[1]
    name = message.text.split(None, 2)[2]
    await add_partner(link, name)
    await log_action(message.chat.id, message.from_user.username or "-", f"AddPartner {link}")
    await message.reply(f"✅ Partner ditambahkan:\n<b>{name}</b>\n🔗 {link}")

@app.on_message(filters.command("delpartner") & filters.group)
async def cmd_delpartner(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Format salah. Gunakan:\n`/delpartner <link_group>`", quote=True)
    link = message.command[1]
    await del_partner(link)
    await log_action(message.chat.id, message.from_user.username or "-", f"DelPartner {link}")
    await message.reply(f"✅ Partner dengan link {link} dihapus.")

@app.on_message(filters.command("listpartner") & filters.group)
async def cmd_listpartner(_, message: Message):
    partners = await list_partners()
    if not partners:
        return await message.reply("📃 Daftar partner kosong.")
    text = "📃 <b>Daftar Partner Group:</b>\n\n"
    for link, name in partners:
        text += f"- <b>{name}</b>: {link}\n"
    await message.reply(text)

@app.on_message(filters.command("logview") & filters.group)
async def cmd_logview(_, message: Message):
    logs = await get_recent_logs(20)
    if not logs:
        return await message.reply("📜 Log aktivitas kosong.")
    text = "📜 <b>Log Aktivitas Terbaru:</b>\n\n"
    for chat_id, username, action, timestamp in logs:
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        text += f"[{time_str}] {username} ({chat_id}): {action}\n"
    await message.reply(text[:4000])

# Tagall otomatis
@app.on_message(filters.group & filters.text)
async def auto_tagall(client, message: Message):
    global last_mention_time
    text = message.text or ""
    links_in_message = re.findall(r"(https?://t.me/\S+)", text)
    if not links_in_message:
        return

    matched_links = await check_links_in_partners(links_in_message)
    if matched_links:
        now = int(time.time())
        if last_mention_time.get(message.chat.id, 0) + MENTION_COOLDOWN > now:
            return  # Masih cooldown

        members = []
        async for member in client.get_chat_members(message.chat.id):
            if not member.user.is_bot:
                members.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
        mention_text = "👥 " + " ".join(members)
        await message.reply(mention_text[:4000], disable_web_page_preview=True)

        last_mention_time[message.chat.id] = now
        await log_action(message.chat.id, message.from_user.username or "-", f"AutoTagAll {len(members)} members")

if __name__ == "__main__":
    asyncio.run(init_db())
    app.run()
