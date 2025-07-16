import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from config import *
from database import *

app = Client("MentionBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# 🔥 Komando Khusus OWNER untuk Izin Akses
@app.on_message(filters.command("akses") & filters.user(OWNER_ID))
async def akses_grant(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("❌ /akses <user_id>")
    user_id = int(m.command[1])
    await grant_akses(user_id)
    await m.reply(f"✅ User {user_id} diberi akses.")

@app.on_message(filters.command("unakses") & filters.user(OWNER_ID))
async def akses_revoke(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("❌ /unakses <user_id>")
    user_id = int(m.command[1])
    await revoke_akses(user_id)
    await m.reply(f"🚫 Akses user {user_id} dicabut.")

@app.on_message(filters.command("akseslist") & filters.user(OWNER_ID))
async def akses_list(_, m: Message):
    users = await list_akses_users()
    if not users:
        return await m.reply("📄 Tidak ada user dengan akses.")
    text = "👥 User dengan Akses:\n\n"
    for uid in users:
        text += f"• <code>{uid}</code>\n"
    await m.reply(text)


# 📦 Manajemen Partner (oleh OWNER atau User Berizin)
@app.on_message(filters.command("addpartner"))
async def add_partner_cmd(_, m: Message):
    user_id = m.from_user.id
    if not await is_user_allowed(user_id):
        return await m.reply("❌ Kamu tidak memiliki izin.")
    if len(m.command) < 3:
        return await m.reply("❌ /addpartner <link> <nama>")
    link = m.command[1]
    name = m.text.split(None, 2)[2]
    await add_partner(link, name)
    await m.reply(f"✅ Partner <b>{name}</b> ditambahkan.")

@app.on_message(filters.command("delpartner"))
async def del_partner_cmd(_, m: Message):
    user_id = m.from_user.id
    if not await is_user_allowed(user_id):
        return await m.reply("❌ Kamu tidak memiliki izin.")
    if len(m.command) < 2:
        return await m.reply("❌ /delpartner <link>")
    link = m.command[1]
    await del_partner(link)
    await m.reply("✅ Partner dihapus.")

@app.on_message(filters.command("listpartner"))
async def list_partner_cmd(_, m: Message):
    partners = await list_partners()
    if not partners:
        return await m.reply("📃 Tidak ada partner.")
    text = "📃 Daftar Partner:\n\n"
    for link, name in partners:
        text += f"• <b>{name}</b>: {link}\n"
    await m.reply(text)


# 📡 Manajemen Grup Target (OWNER)
@app.on_message(filters.command("addgrup"))
async def addgrup_cmd(_, m: Message):
    if m.chat.type in ["group", "supergroup"]:
        if m.from_user.id != OWNER_ID:
            return await m.reply("❌ Hanya OWNER yang dapat menambahkan grup.")
        await add_group(m.chat.id)
        return await m.reply("✅ Grup ini telah ditambahkan ke daftar target.")
    if m.from_user.id == OWNER_ID and len(m.command) >= 2:
        chat_id = int(m.command[1])
        await add_group(chat_id)
        return await m.reply(f"✅ Grup {chat_id} ditambahkan.")
    await m.reply("❌ Gunakan di grup langsung atau /addgrup <chat_id>.")

@app.on_message(filters.command("delgrup") & filters.user(OWNER_ID))
async def delgrup_cmd(_, m: Message):
    if m.chat.type in ["group", "supergroup"]:
        await del_group(m.chat.id)
        return await m.reply("✅ Grup ini dihapus dari target.")
    if len(m.command) >= 2:
        chat_id = int(m.command[1])
        await del_group(chat_id)
        return await m.reply(f"✅ Grup {chat_id} dihapus.")
    await m.reply("❌ Gunakan di grup langsung atau /delgrup <chat_id>.")

@app.on_message(filters.command("listgrup") & filters.user(OWNER_ID))
async def listgrup_cmd(_, m: Message):
    groups = await list_groups()
    if not groups:
        return await m.reply("📃 Tidak ada grup target.")
    text = "📃 Daftar Grup Target:\n\n"
    for g in groups:
        text += f"• <code>{g}</code>\n"
    await m.reply(text)


# 🚀 Auto Mention Saat PM
@app.on_message(filters.private & filters.text)
async def trigger_mentions(_, m: Message):
    if not await is_partner_link(m.text):
        return await m.reply("❌ Ini bukan link partner resmi.")
    groups = await list_groups()
    if not groups:
        return await m.reply("⚠️ Tidak ada grup target.")
    await m.reply(f"📡 Link partner valid.\nMengirim mention di {len(groups)} grup...")

    for group_id in groups:
        if await can_mention(group_id, MENTION_COOLDOWN):
            try:
                members = []
                async for mem in app.get_chat_members(group_id):
                    if not mem.user.is_bot:
                        members.append(f"[{mem.user.first_name}](tg://user?id={mem.user.id})")
                msg = f"📣 {m.text}\n\n" + " ".join(members)
                await app.send_message(group_id, msg[:4000], disable_web_page_preview=True)
                await update_cooldown(group_id)
                await log_action(group_id, f"TagAll from {m.from_user.id}")
            except Exception as e:
                print(f"❌ Gagal mention di {group_id}: {e}")

    await m.reply("✅ Mention selesai dikirim ke semua grup.")

# 🔰 Start Bot
@app.on_message(filters.command("start"))
async def start_message(_, m: Message):
    await m.reply("🤖 Bot aktif.\nGunakan /addpartner jika kamu memiliki akses.\nKirim link partner resmi di sini untuk mention otomatis.")

async def main():
    await init_db()
    await app.start()
    try:
        await app.send_message(OWNER_ID, "🚀 Bot berhasil diaktifkan.")
    except:
        pass
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
