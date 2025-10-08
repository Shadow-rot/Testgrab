
import urllib.request
from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from Grabber import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if str(user.id) not in sudo_users:
        await update.message.reply_text("⚠️ Only my Sensei can delete characters.")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("❌ Use format: /delete <id>")
        return

    try:
        char_id = args[0]
        character = await collection.find_one_and_delete({"id": char_id})

        if not character:
            await update.message.reply_text("❌ Character not found in database.")
            return

        # Try deleting from channel
        try:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character["message_id"])
            await update.message.reply_text(f"✅ Character ID {char_id} deleted successfully.")
        except:
            await update.message.reply_text("⚠️ Deleted from DB but not found in channel.")

    except Exception as e:
        await update.message.reply_text(f"❌ Error deleting character: {e}")


DELETE_HANDLER = CommandHandler("delete", delete)
application.add_handler(DELETE_HANDLER)