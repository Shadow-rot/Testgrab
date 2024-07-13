from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from shivu import (application, PHOTO_URL, OWNER_ID,
                    user_collection, top_global_groups_collection, top_global_groups_collection, 
                    group_user_totals_collection)


async def stats2(update: Update, context: CallbackContext) -> None:
    user_count = await user_collection.count_documents({})

    group_count = len(await group_user_totals_collection.distinct('group_id'))

    await update.message.reply_text(f'Total Users: {user_count}\nTotal Groups: {group_count}')

application.add_handler(CommandHandler("stats1", stats2, block=False))
