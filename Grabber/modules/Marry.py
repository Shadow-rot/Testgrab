import asyncio
from pyrogram import filters, Client, types as t
from shivu import shivuu as bot
from shivu import user_collection, collection

DEVS = (7370080350)

async def get_unique_characters(receiver_id, target_rarities=['🟢 Common' , '🔵 Medium' , '🟠 Rare' , '🟡 Legendary']):
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

import time

# Dictionary to store last roll time for each user
cooldowns = {}

@bot.on_message(filters.command(["dice", "marry"]))
async def dice(_: bot, message: t.Message):
    chat_id = message.chat.id
    mention = message.from_user.mention
    user_id = message.from_user.id

    # Check if the user is in cooldown
    if user_id in cooldowns and time.time() - cooldowns[user_id] < 60:  # Adjust the cooldown time (in seconds)
        cooldown_time = int(60 - (time.time() - cooldowns[user_id]))
        return await message.reply_text(f"Please wait {cooldown_time} seconds before rolling again.", quote=True)

    # Update the last roll time for the user
    cooldowns[user_id] = time.time()

    if user_id == 7162166061:
        return await message.reply_text(f"Sorry {mention} You are banned from using this command.")

    elif user_id == 6600178006:
        receiver_id = message.from_user.id
        unique_characters = await get_unique_characters(receiver_id)
        try:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': {'$each': unique_characters}}})
            img_urls = [character['img_url'] for character in unique_characters]
            captions = [
                f"congratulations! {mention} you are now married your girl is ready on bed sorry mean harem 💍!\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                for character in unique_characters
            ]
            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)
        except Exception as e:
            print(e)
    else:
        receiver_id = message.from_user.id
   
        unique_characters = await get_unique_characters(receiver_id)

        xx = await bot.send_dice(chat_id=chat_id)
        value = int(xx.dice.value)

        if value == 1 or value == 6:
            for character in unique_characters:
                try:
                    await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': character}})
                except Exception as e:
                    print(e)  # Handle the exception appropriately

            img_urls = [character['img_url'] for character in unique_characters]
            captions = [
                f"congratulations! {mention} You are now married your girl is ready on bed sorry i mean harem  💍!\n"
                f"Name: {character['name']}\n"
                f"Rarity: {character['rarity']}\n"
                f"Anime: {character['anime']}\n"
                for character in unique_characters
            ]

            for img_url, caption in zip(img_urls, captions):
                await message.reply_photo(photo=img_url, caption=caption)

            return

        else:
            await message.reply_text(f"fuck she is rejected your married proposal and run away 🤡", quote=True)
            return
