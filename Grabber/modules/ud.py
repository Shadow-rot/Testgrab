import urllib.request
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from Grabber import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

async def update_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if str(user.id) not in sudo_users:
        await update.message.reply_text("⚠️ Only my Sensei can use this command.")
        return

    args = context.args
    if len(args) != 3:
        await update.message.reply_text("❌ Format: /update <id> <field> <new_value>")
        return

    char_id, field, new_value = args

    valid_fields = ["img_url", "name", "anime", "rarity"]
    if field not in valid_fields:
        await update.message.reply_text(f"⚠️ Invalid field. Use: {', '.join(valid_fields)}")
        return

    # Find character
    character = await collection.find_one({"id": char_id})
    if not character:
        await update.message.reply_text("❌ Character not found.")
        return

    if field == "rarity":
        try:
            new_value = RARITY_MAP[int(new_value)]
        except (KeyError, ValueError):
            await update.message.reply_text("❌ Invalid rarity number (1–6).")
            return
    elif field in ["name", "anime"]:
        new_value = new_value.replace("-", " ").title()

    await collection.find_one_and_update({"id": char_id}, {"$set": {field: new_value}})

    # Update caption in channel
    try:
        new_caption = (
            f"<b>Character Name:</b> {character.get('name') if field!='name' else new_value}\n"
            f"<b>Anime:</b> {character.get('anime') if field!='anime' else new_value}\n"
            f"<b>Rarity:</b> {character.get('rarity') if field!='rarity' else new_value}\n"
            f"<b>ID:</b> {char_id}\n"
            f"Updated by <a href='tg://user?id={user.id}'>{user.first_name}</a>"
        )

        await context.bot.edit_message_caption(
            chat_id=CHARA_CHANNEL_ID,
            message_id=character["message_id"],
            caption=new_caption,
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ Character updated successfully.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Updated in DB but failed to update caption.\nError: {e}")


UPDATE_HANDLER = CommandHandler("update", update_character)
application.add_handler(UPDATE_HANDLER)