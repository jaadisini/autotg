import asyncio
import re
import time
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import *

app = Client("AutoMentionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📖 Menu Bantuan", callback_data="help_menu")]])
    await message.reply("🤖 Bot siap membantu mention otomatis grup partner!", reply_markup=buttons)

@app.on_message(filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply("""
<b>📖 Perintah Bot:</b>

/addpartner <link> <nama> - Tambahkan partner
/delpartner <link> - Hapus partner
/listpartner - Lihat daftar partner
/logview - Lihat log aktivitas
""")

@app.on_callback_query(filters.regex("help_menu"))
async def help_callback(_, query):
    await query.message.edit_text("""
<b>📖 Perintah Bot:</b>

/addpartner <link> <nama> - Tambahkan partner
/delpartner <link> - Hapus partner
/listpartner - Lihat daftar partner
/logview - Lihat log aktivitas
""")

@app.on_message(filters.command("addpartner") & filters.group)
async def addpartner_cmd(_, message: Message):
    if len(message.command) < 3:
        return await message.reply("❌ Format salah. Gunakan:\n/addpartner <link> <nama>")
    link = message.command[1]
    name = message.text.split(None, 2)[2]
    await add_partner(link, name)
    await log_action(message.chat.id, message.from_user.username or "-", f"Tambah partner: {link}")
    await message.reply(f"✅ Partner <b>{name}</b> ditambahkan.")

@app.on_message(filters.command("delpartner") & filters.group)
async def delpartner_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Gunakan: /delpartner <link>")
    link = message.command[1]
    await del_partner(link)
    await log_action(message.chat.id, message.from_user.username or "-", f"Hapus partner: {link}")
    await message.reply("✅ Partner dihapus.")

@app.on_message(filters.command("listpartner") & filters.group)
async def listpartner_cmd(_, message: Message):
    partners = await list_partners()
    if not partners:
        return await message.reply("📃 Tidak ada partner.")
    text = "📃 <b>Daftar Partner:</b>\n\n"
    for link, name in partners:
        text += f"• <b>{name}</b>: {link}\n"
    await message.reply(text)

@app.on_message(filters.command("logview") & filters.group)
async def logview_cmd(_, message: Message):
    logs = await get_recent_logs()
    if not logs:
        return await message.reply("📜 Log aktivitas kosong.")
    text = "<b>📜 Log Aktivitas:</b>\n\n"
    for chat_id, username, action, timestamp in logs:
        t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        text += f"[{t}] {username}: {action}\n"
    await message.reply(text[:4000])

@app.on_message(filters.group & filters.text)
async def auto_mention(client, message: Message):
    text = message.text or ""
    links_found = await check_links_in_partners(text)

    if links_found and await can_mention(message.chat.id, MENTION_COOLDOWN):
        members = []
        async for m in client.get_chat_members(message.chat.id):
            if not m.user.is_bot:
                members.append(f"[{m.user.first_name}](tg://user?id={m.user.id})")

        mention_text = "👥 " + " ".join(members)
        await message.reply(mention_text[:4000], disable_web_page_preview=True)
        await update_cooldown(message.chat.id)
        await log_action(message.chat.id, message.from_user.username or "-", f"TagAll {len(members)} member")

        try:
            await client.send_message(
                LOG_CHAT_ID,
                f"📢 <b>TagAll Dikirim</b>\n• Grup: <b>{message.chat.title}</b>\n• Oleh: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n• Link partner: {', '.join(links_found)}"
            )
        except:
            pass

async def main():
    await init_db()
    await app.start()

    try:
        await app.send_message(OWNER_ID, "🚀 Bot berhasil di-deploy dan siap digunakan.")
    except:
        print("⚠️ Gagal kirim notifikasi ke owner.")

    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
