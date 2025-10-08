import random
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from Grabber import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from Grabber import pm_users as collection 


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        
        await context.bot.send_message(chat_id=GROUP_ID, 
                                       text=f"New user Started The Bot..\n User: <a href='tg://user?id={user_id}'>{escape(first_name)})</a>", 
                                       parse_mode='HTML')
    else:
        
        if user_data['first_name'] != first_name or user_data['username'] != username:
            
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    

    if update.effective_chat.type== "private":
        
        
        caption = f"""
        ***𝙷𝚊𝚕𝚕𝚘***

***𝗛𝗼𝗹𝗮 𝗛𝗼𝗹𝗮! ,["⁧;[" ✨

        ᴇᴍʙᴀʀᴋ ᴏɴ ᴀɴ ᴇxʜɪʟᴀʀᴀᴛɪɴɢ ᴊᴏᴜʀɴᴇʏ ᴛʜʀᴏᴜɢʜ ᴛʜᴇ ᴡᴏʀʟᴅ ᴏꜰ ᴀɴɪᴍᴇ! ɪ'ᴍ ʏᴏᴜʀ ɢᴜɪᴅᴇ ᴛᴏ ᴄᴀᴘᴛᴜʀɪɴɢ ᴀɴᴅ ᴄᴏʟʟᴇᴄᴛɪɴɢ ᴀ ᴅɪᴠᴇʀꜱᴇ ᴀʀʀᴀʏ ᴏꜰ ᴠɪʙʀᴀɴᴛ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ. ᴇɴɢᴀɢᴇ ɪɴ ᴄʜᴀʟʟᴇɴɢᴇꜱ, ᴛʀᴀᴅᴇ ᴡɪᴛʜ ꜰᴇʟʟᴏᴡ ᴇɴᴛʜᴜꜱɪᴀꜱᴛꜱ, ᴀɴᴅ ʙᴜɪʟᴅ ʏᴏᴜʀ ᴜʟᴛɪᴍᴀᴛᴇ ᴀɴɪᴍᴇ ᴄᴏʟʟᴇᴄᴛɪᴏɴ. ʟᴇᴛ'ꜱ ᴅɪᴠᴇ ɪɴᴛᴏ ᴛʜɪꜱ ᴀᴅᴠᴇɴᴛᴜʀᴇ ᴛᴏɢᴇᴛʜᴇʀ


ʜɪᴛ help ᴛᴏ ғɪɴᴅ ᴏᴜᴛ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ***
        """
        
        keyboard = [
            [InlineKeyboardButton("sᴛᴀʀᴛ ɢᴜᴇssɪɴɢ💫", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("🏥𝚂𝚄𝙿𝙿𝙾𝚁𝚃", url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton("✨sᴇɴsᴇɪ✨", url=f'https://t.me/AKIRA_ISHIKKI')],
            [InlineKeyboardButton("⚙️ʜᴇʟᴘ", callback_data='help')],
            [InlineKeyboardButton("ᴄʀᴇᴅɪᴛs👾", url=f'https://telegra.ph/ᴄʀᴇᴅɪᴛs-06-24')],
            [InlineKeyboardButton("Fᴏᴜɴᴅᴇʀs👾", url=f'https://telegra.ph/ᴄʀᴇᴅɪᴛs-06-24')],
            [InlineKeyboardButton("Lᴏɢs🎧", url=f'https://t.me/LovelyXNetwork')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)

        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption=caption, reply_markup=reply_markup, parse_mode='markdown')

    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
         [InlineKeyboardButton("sᴛᴀʀᴛ ɢᴜᴇssɪɴɢ💫", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("🏥𝚂𝚄𝙿𝙿𝙾𝚁𝚃", url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton("✨sᴇɴsᴇɪ✨", url=f'https://t.me/AKIRA_ISHIKKI')],
            [InlineKeyboardButton("⚙️ʜᴇʟᴘ", callback_data='help')],
            [InlineKeyboardButton("ᴄʀᴇᴅɪᴛs👾", url=f'https://telegra.ph/ᴄʀᴇᴅɪᴛs-06-24')],
            [InlineKeyboardButton("Fᴏᴜɴᴅᴇʀs👾", url=f'https://telegra.ph/ᴄʀᴇᴅɪᴛs-06-24')],
            [InlineKeyboardButton("Lᴏɢs🎧", url=f'https://t.me/LovelyXNetwork')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_url, caption="🎴Alive!?... \n connect to me in PM For more information ",reply_markup=reply_markup )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
    ***Help Section:***
    
***/guess: To Guess character (only works in group)***
***/fav: Add Your fav***
***/trade : To trade Characters***
***/gift: Give any Character from Your Collection to another user.. (only works in groups)***
***/collection: To see Your Collection***
***/topgroups : See Top Groups.. Ppl Guesses Most in that Groups***
***/top: Too See Top Users***
***/ctop : Your ChatTop***
***/changetime: Change Character appear time (only works in Groups)***
   """
        help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)
        
        await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=query.message.message_id, caption=help_text, reply_markup=reply_markup, parse_mode='markdown')

    elif query.data == 'back':

        caption = f"""
        ***𝙷𝚊𝚕𝚕𝚘*** ✨

***◎ ─━──━─❖─━──━─ ◎

⍟ ɪ ᴀᴍ 𝙶𝚄𝙴𝚂𝚂 em all 𝙱𝙾𝚃 ʙᴏᴛ ɪ sᴘᴀᴡɴ ᴀɴɪᴍᴇ ᴄʜᴀʀᴀᴄᴛᴇʀs
ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘs, ᴀɴᴅ ʟᴇᴛ ᴜsᴇʀs ᴄᴏʟʟᴇᴄᴛ ᴛʜᴇᴍ
⍟ sᴏ ᴡʜᴀᴛ ᴀʀᴇ ʏᴏᴜ ᴡᴀɪᴛɪɴɢ ғᴏʀ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ
ʙʏ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ

◎ ─━──━─❖─━──━─ ◎

ʜɪᴛ help ᴛᴏ ғɪɴᴅ ᴏᴜᴛ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ***
        """

        
        keyboard = [
            [InlineKeyboardButton("◆𝙰𝙳𝙳 𝙼𝙴◆", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("Sᴜᴘᴘᴏʀᴛ", url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton("Lᴏɢs", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("★ʜᴇʟᴘ★", callback_data='help')],
            [InlineKeyboardButton("▣ᴄʀᴇᴅɪᴛs▣", url=f'https://telegra.ph/ᴄʀᴇᴅɪᴛs-06-24')]
            [InlineKeyboardButton("▣Fᴏᴜɴᴅᴇʀs▣", url=f'https://telegra.ph/ᴄʀᴇᴅɪᴛs-06-24')]
            [InlineKeyboardButton("▣ɴᴇᴛᴡᴏʀᴋ▣", url=f'https://t.me/LovelyXNetwork')]
            [InlineKeyboardButton("▣sᴇɴsᴇɪ▣", url=f'https://t.me/AKIRA_ISHIKKI')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(chat_id=update.effective_chat.id, message_id=query.message.message_id, caption=caption, reply_markup=reply_markup, parse_mode='markdown')


application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
