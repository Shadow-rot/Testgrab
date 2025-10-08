import aiohttp
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from Grabber import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

RARITY_MAP = {
    1: "⚪ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💮 Limited",
    6: "🧬 X-verse"
}

WRONG_FORMAT = """❌ Wrong format!
Use either:

<b>Via URL:</b>
<code>/upload [img_url] [character-name] [anime-name] [rarity]</code>

<b>Or by reply:</b>
Reply to a photo/video/document and type:
<code>/upload [character-name] [anime-name] [rarity]</code>

<b>Rarity Map:</b>
1 = ⚪ Common  
2 = 🟣 Rare  
3 = 🟡 Legendary  
4 = 🟢 Medium  
5 = 💮 Limited  
6 = 🧬 X-verse
"""

# Generate sequential ID
async def get_next_sequence_number(sequence_name: str):
    seq_collection = db.sequences
    seq_doc = await seq_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not seq_doc:
        await seq_collection.insert_one({'_id': sequence_name, 'sequence_value': 1})
        return 1
    return seq_doc['sequence_value']


# Better URL validator — works with Catbox, Telegraph, Imgur, etc.
async def is_valid_url(url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                return resp.status == 200
    except Exception:
        return False


# Main upload command
async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if str(user.id) not in sudo_users:
        await update.message.reply_text("⚠️ Ask my Sensei for permission.")
        return

    message = update.message
    args = context.args

    try:
        # === Case 1: Reply Upload ===
        if message.reply_to_message and len(args) == 3:
            reply = message.reply_to_message
            char_name = args[0].replace("-", " ").title()
            anime_name = args[1].replace("-", " ").title()

            try:
                rarity = RARITY_MAP[int(args[2])]
            except (KeyError, ValueError):
                await message.reply_text("❌ Invalid rarity number. Use 1–6.")
                return

            # Handle multiple media types
            file = None
            if reply.photo:
                file = await reply.photo[-1].get_file()
            elif reply.video:
                file = await reply.video.get_file()
            elif reply.document:
                file = await reply.document.get_file()
            elif reply.animation:
                file = await reply.animation.get_file()
            else:
                await message.reply_text("⚠️ Unsupported media type. Reply to photo/video/document.")
                return

            img_url = file.file_path

        # === Case 2: URL Upload ===
        elif len(args) == 4:
            img_url = args[0]
            char_name = args[1].replace("-", " ").title()
            anime_name = args[2].replace("-", " ").title()

            valid = await is_valid_url(img_url)
            if not valid:
                await message.reply_text("❌ Invalid or inaccessible image URL (check link).")
                return

            try:
                rarity = RARITY_MAP[int(args[3])]
            except (KeyError, ValueError):
                await message.reply_text("❌ Invalid rarity number. Use 1–6.")
                return

        else:
            await message.reply_html(WRONG_FORMAT)
            return

        # === Generate ID ===
        char_id = str(await get_next_sequence_number("character_id")).zfill(3)

        # === Character Data ===
        character = {
            "img_url": img_url,
            "name": char_name,
            "anime": anime_name,
            "rarity": rarity,
            "id": char_id
        }

        # === Send to Channel ===
        try:
            msg = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=img_url,
                caption=(
                    f"<b>Character Name:</b> {char_name}\n"
                    f"<b>Anime:</b> {anime_name}\n"
                    f"<b>Rarity:</b> {rarity}\n"
                    f"<b>ID:</b> {char_id}\n"
                    f"Added by <a href='tg://user?id={user.id}'>{user.first_name}</a>"
                ),
                parse_mode="HTML"
            )
            character["message_id"] = msg.message_id
            await collection.insert_one(character)
            await message.reply_text("✅ Character uploaded successfully!")

        except Exception as e:
            await collection.insert_one(character)
            await message.reply_text(f"⚠️ Added to DB but failed to send to channel.\nError: {e}")

    except Exception as e:
        await message.reply_text(f"❌ Upload failed.\nError: {e}\nContact {SUPPORT_CHAT}")


UPLOAD_HANDLER = CommandHandler("upload", upload)
application.add_handler(UPLOAD_HANDLER)