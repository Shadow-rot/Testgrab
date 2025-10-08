from pyrogram import Client, filters
from Grabber import (
    db,
    collection,
    user_collection,
    shivuu as app,
    sudo_users,
)
import asyncio
import logging

logger = logging.getLogger(__name__)

DEV_LIST = sudo_users  # use your sudo list

# --------------------------- Helper: Give Character --------------------------- #

async def give_character(receiver_id: int, character_id: str):
    """Give a character to a specific user ID."""
    character = await collection.find_one(
        {"id": character_id},
        {"_id": 0, "id": 1, "rarity": 1, "anime": 1, "name": 1, "img_url": 1},
    )

    if not character:
        raise ValueError("❌ Character not found.")

    # Ensure user document exists
    await user_collection.update_one(
        {"id": receiver_id}, {"$setOnInsert": {"characters": []}}, upsert=True
    )

    # Add character (prevent duplicates)
    await user_collection.update_one(
        {"id": receiver_id},
        {"$addToSet": {"characters": character}},
    )

    caption = (
        f"✅ <b>Character Given Successfully!</b>\n\n"
        f"👤 <b>User:</b> <code>{receiver_id}</code>\n"
        f"🎭 <b>Name:</b> {character['name']}\n"
        f"🎬 <b>Anime:</b> {character['anime']}\n"
        f"💫 <b>Rarity:</b> {character['rarity']}\n"
        f"🆔 <b>ID:</b> <code>{character['id']}</code>"
    )

    return character.get("img_url"), caption


@app.on_message(filters.command("give") & filters.reply & filters.user(DEV_LIST))
async def give_character_command(client: Client, message):
    """Give a character to the replied user."""
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a user to give a character.")
        return

    try:
        _, character_id = message.text.split(maxsplit=1)
    except ValueError:
        await message.reply_text("❌ Usage: <code>/give &lt;character_id&gt;</code>")
        return

    receiver_id = message.reply_to_message.from_user.id

    try:
        img_url, caption = await give_character(receiver_id, character_id)
        if img_url:
            await message.reply_photo(img_url, caption=caption, quote=True)
        else:
            await message.reply_text(caption, quote=True)
    except Exception as e:
        logger.exception("Give command error:")
        await message.reply_text(f"❌ Error: {e}")

# --------------------------- Helper: Add All Characters --------------------------- #

async def add_all_characters_for_user(user_id: int):
    """Give all characters in collection to a user (only new ones)."""
    all_characters = await collection.find(
        {}, {"_id": 0, "id": 1, "name": 1, "anime": 1, "rarity": 1, "img_url": 1}
    ).to_list(length=None)

    if not all_characters:
        return "⚠️ No characters found in database."

    # ensure user doc
    await user_collection.update_one(
        {"id": user_id}, {"$setOnInsert": {"characters": []}}, upsert=True
    )

    # $addToSet with $each ensures no duplicates
    await user_collection.update_one(
        {"id": user_id},
        {"$addToSet": {"characters": {"$each": all_characters}}},
    )

    return f"✅ All characters have been added for user <code>{user_id}</code>."


@app.on_message(filters.command("add") & filters.user(DEV_LIST))
async def add_characters_command(client: Client, message):
    """Add all characters for yourself (admin only)."""
    user_id = message.from_user.id
    try:
        result = await add_all_characters_for_user(user_id)
        await message.reply_text(result)
    except Exception as e:
        logger.exception("Add command error:")
        await message.reply_text(f"❌ Failed: {e}")

# --------------------------- Helper: Kill Character --------------------------- #

async def kill_character(receiver_id: int, character_id: str):
    """Remove a specific character from user."""
    result = await user_collection.update_one(
        {"id": receiver_id},
        {"$pull": {"characters": {"id": character_id}}},
    )

    if result.modified_count == 0:
        raise ValueError("⚠️ Character not found in user's list.")

    return (
        f"🗑️ Successfully removed character <code>{character_id}</code> "
        f"from user <code>{receiver_id}</code>."
    )


@app.on_message(filters.command("kill") & filters.reply & filters.user(DEV_LIST))
async def remove_character_command(client: Client, message):
    """Remove a character from a replied user."""
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to a user to remove a character.")
        return

    try:
        _, character_id = message.text.split(maxsplit=1)
    except ValueError:
        await message.reply_text("❌ Usage: <code>/kill &lt;character_id&gt;</code>")
        return

    receiver_id = message.reply_to_message.from_user.id

    try:
        result = await kill_character(receiver_id, character_id)
        await message.reply_text(result)
    except Exception as e:
        logger.exception("Kill command error:")
        await message.reply_text(f"❌ Error: {e}")