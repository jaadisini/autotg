import re
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID, LOG_CHAT_ID
from database import *

app = Client("TagAllBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_cmd(_, message: Message):
    buttons = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📖 Menu Bantuan", callback_data="help_menu")]]
    )
    await message.reply("👋 Halo! Saya bot mention otomatis.\nGunakan di grup mutualan kamu!", reply_markup=buttons)

@app.on_message(filters.command("help"))
async def help_cmd(_, message: Message):
    await message.reply("""
<b>📖 Bantuan Bot TagAll</b>

✅ Otomatis tag semua member saat mendeteksi link partner.

🛠 Perintah Admin:
• /addpartner <link> <nama>
• /delpartner <link>
• /listpartner
• /logview

🎛 Umum:
• /start — Tampilkan menu
• /help — Lihat bantuan
""")

@app.on_callback_query(filters.regex("help_menu"))
async def callback_help(_, query):
    await query.message.edit("""
<b>📖 Bantuan Bot TagAll</b>

✅ Otomatis tag semua member saat mendeteksi link partner.

🛠 Perintah Admin:
• /addpartner <link> <nama>
• /delpartner <link>
• /listpartner
• /logview

🎛 Umum:
• /start — Tampilkan menu
• /help — Lihat bantuan
""")

@app.on_message(filters.command("addpartner") & filters.group)
async def addpartner_cmd(_, message: Message):
    if len(message.command) < 3:
        return await message.reply("❌ Format salah. Gunakan: /addpartner <link> <nama>")
    link = message.command[1]
    name = message.text.split(None, 2)[2]
    await add_partner(link, name)
    await insert_log("addpartner", message.chat.id, message.from_user.id, f"{name} ({link})")
    await message.reply(f"✅ Partner <b>{name}</b> ditambahkan.")

@app.on_message(filters.command("delpartner") & filters.group)
async def delpartner_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Gunakan: /delpartner <link>")
    link = message.command[1]
    await del_partner(link)
    await insert_log("delpartner", message.chat.id, message.from_user.id, link)
    await message.reply("✅ Partner dihapus.")

@app.on_message(filters.command("listpartner") & filters.group)
async def listpartner_cmd(_, message: Message):
    partners = await list_partners()
    if not partners:
        return await message.reply("📃 Belum ada partner.")
    text = "📃 <b>Daftar Partner:</b>\n\n"
    for link, name in partners:
        text += f"• <b>{name}</b>: {link}\n"
    await message.reply(text)

@app.on_message(filters.command("logview") & filters.group)
async def logview_cmd(_, message: Message):
    logs = await get_logs()
    if not logs:
        return await message.reply("📭 Belum ada aktivitas.")
    text = "<b>📑 Log Aktivitas Terbaru:</b>\n\n"
    for e, t, chat, user, detail in logs:
        text += f"• [{e.upper()}] — <code>{t.split('T')[0]}</code>\n  👤 User ID: <code>{user}</code>\n  💬 Detail: {detail}\n\n"
    await message.reply(text[:4000])

@app.on_message(filters.group & filters.text)
async def mention_handler(client, message: Message):
    text = message.text or ""
    links = re.findall(r"(https?://t.me/\S+)", text)
    if not links:
        return
    matched = await check_links_in_partners(links)
    if matched and await can_mention(message.chat.id):
        members = []
        async for member in client.get_chat_members(message.chat.id):
            if not member.user.is_bot:
                members.append(f"[{member.user.first_name}](tg://user?id={member.user.id})")
        tag_text = "👥 " + " ".join(members)
        await message.reply(tag_text[:4000], disable_web_page_preview=True)
        await insert_log("tagall", message.chat.id, message.from_user.id, f"{len(members)} users")
        await update_cooldown(message.chat.id)
        try:
            await client.send_message(
                LOG_CHAT_ID,
                f"📢 TagAll Terkirim\n🧑‍💼 Oleh: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n📍 Grup: <b>{message.chat.title}</b>\n🔗 Link terdeteksi: {', '.join(matched)}",
                disable_web_page_preview=True,
            )
        except:
            pass

async def main():
    print("🔄 Inisialisasi database...")
    await init_db()
    await app.start()
    print("✅ Bot online.")

    try:
        await app.send_message(OWNER_ID, "🚀 Bot berhasil di-deploy dan siap digunakan.")
        print("✅ Notifikasi dikirim ke owner.")
    except Exception as e:
        print(f"⚠️ Gagal kirim notifikasi ke owner: {e}")

    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
