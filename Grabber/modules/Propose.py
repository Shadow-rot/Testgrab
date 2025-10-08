import asyncio
import time
import random

from pyrogram import filters, Client, types as t

from Grabber import shivuu as bot
from Grabber import user_collection, collection

DEVS = (5116239739)

async def get_unique_characters(receiver_id, target_rarities=['⚪️', '🔴', '🟣', '🟡', '💮', '🫧']):
    try:
        pipeline = [
            {'$match': {'rarity': {'$in': target_rarities}, 'id': {'$nin': [char['id'] for char in (await user_collection.find_one({'id': receiver_id}, {'characters': 1}))['characters']]}}},
            {'$sample': {'size': 1}}  # Adjust Num
        ]

        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        return characters
    except Exception as e:
        return []

# Dictionary to store last roll time for each user
last_propose_times = {}

@bot.on_message(filters.command(["propose"]))
async def propose(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Check if the user is in cooldown
    if user_id in last_propose_times and time.time() - last_propose_times[user_id] < 300:  # Adjust the cooldown time (in seconds)
        last_propose_time = int(300 - (time.time() - last_propose_times[user_id]))
        return await message.reply_text(f"Cooldown! You can propose again in  {last_propose_time}.", quote=True)

    proposal_message = "ғɪɴᴀʟʟʏ ᴛʜᴇ ᴛɪᴍᴇ ᴛᴏ ᴘʀᴏᴘᴏsᴇ"
    photo_path = 'https://te.legra.ph/file/4d0f83726fe8cd637d3ff.jpg'
    await message.reply_photo(photo=photo_path, caption=proposal_message)
    await asyncio.sleep(2)

    # Send the proposal text
    await message.reply_text("ᴘʀᴏᴘᴏsɪɴɢ.....🥀")
    await asyncio.sleep(2)

    # Generate a random result
    if random.random() < 0.6:
        rejection_message = "fuck she is rejected your married proposal and run away 😂"
        rejection_photo_path = 'https://graph.org/file/48c147582d2742105e6ec.jpg'
        await message.reply_photo(photo=rejection_photo_path, caption=rejection_message)
    else:
        receiver_id = message.from_user.id
        unique_characters = await get_unique_characters(receiver_id)
        try:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})
            img_urls = [character['img_url'] for character in unique_characters]
            captions = [
                f"𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗦𝗵𝗲 𝗮𝗰𝗰𝗲𝗽𝘁𝗲𝗱 𝘆𝗼𝘂.🤩 𝗨𝗿 𝗴𝗶𝗿𝗹 𝗶𝘀 𝗿𝗲𝗮𝗱𝘆 𝗶𝗻 𝗯𝗲𝗱 𝗜 𝗺𝗲𝗮𝗻 𝗵𝗮𝗿𝗲𝗺! {mention}, {character['name']}❤️\n\n"
                f"☘️ 𝙉𝙖𝙢𝙚: {character['name']}\n"
                f"🏵 𝙍𝙖𝙧𝙞𝙩𝙮: {character['rarity']}\n"
                f"💍 𝘼𝙣𝙞𝙢𝙚: {character['anime']}\n"
                for character in unique_characters
            ]
            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)
        except Exception as e:
            print(e)
    
    last_propose_times[user_id] = time.time()
