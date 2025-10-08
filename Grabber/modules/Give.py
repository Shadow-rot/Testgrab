import logging
from typing import Tuple, Optional

from pyrogram import filters
from pyrogram.types import Message
from Grabber import (
    db,
    collection,
    user_collection,
    shivuu as app,
    sudo_users,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Use your sudo list (fallback to provided list if not present)
DEV_LIST = sudo_users if 'sudo_users' in globals() else [5147822244]


# -------------------- Helper functions -------------------- #
async def _fetch_character_min(character_id: str) -> Optional[dict]:
    """Return a small dict for character or None."""
    char = await collection.find_one(
        {'id': character_id},
        projection={'_id': 0, 'id': 1, 'name': 1, 'anime': 1, 'rarity': 1, 'img_url': 1}
    )
    return char


async def _ensure_user_doc(user_id: int):
    """Ensure the user doc exists with characters array."""
    await user_collection.update_one(
        {'id': user_id},
        {'$setOnInsert': {'id': user_id, 'characters': []}},
        upsert=True
    )


# -------------------- /give -------------------- #
async def give_character(receiver_id: int, character_id: str) -> Tuple[str, str, bool]:
    """
    Add a character object to user's characters array.
    Returns: (img_url, caption, added_flag)
    Raises ValueError if character not found.
    """
    char = await _fetch_character_min(character_id)
    if not char:
        raise ValueError("❌ Character not found.")

    # ensure user doc exists
    await _ensure_user_doc(receiver_id)

    # use $addToSet to avoid duplicates (object equality)
    res = await user_collection.update_one(
        {'id': receiver_id},
        {'$addToSet': {'characters': char}}
    )

    added = (res.modified_count > 0)  # True if actually added (not already present)

    caption = (
        f"✅ <b>Character Given</b>\n\n"
        f"👤 <b>User:</b> <code>{receiver_id}</code>\n"
        f"🎭 <b>Name:</b> {char.get('name')}\n"
        f"🎬 <b>Anime:</b> {char.get('anime')}\n"
        f"💫 <b>Rarity:</b> {char.get('rarity')}\n"
        f"🆔 <b>ID:</b> <code>{char.get('id')}</code>\n\n"
        + ("➕ Added to user's collection." if added else "⚠️ User already had this character.")
    )

    img_url = char.get('img_url')
    return img_url, caption, added


@app.on_message(filters.command("give") & filters.reply)
async def give_character_command(client, message: Message):
    # permission check
    sender_id = message.from_user.id
    if sender_id not in DEV_LIST:
        await message.reply_text("⛔ You are not authorized to use this command.")
        return

    # must reply to a user message
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("⚠️ Reply to a user's message to give a character.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply_text("❌ Usage: /give <character_id>  (reply to target user's message)")
        return

    character_id = parts[1].strip()
    receiver_id = message.reply_to_message.from_user.id

    try:
        img_url, caption, added = await give_character(receiver_id, character_id)

        # Try to send preview with image; fallback to text if sending fails
        try:
            if img_url:
                # try photo first; if it fails (not an image), send as document
                try:
                    await message.reply_photo(photo=img_url, caption=caption, parse_mode='html', quote=True)
                except Exception:
                    await message.reply_document(document=img_url, caption=caption, parse_mode='html', quote=True)
            else:
                await message.reply_text(caption, parse_mode='html', quote=True)
        except Exception as exc_send:
            logger.exception("Failed to send preview in /give")
            # Even if preview fails, still inform admin with caption
            await message.reply_text(caption, parse_mode='html', quote=True)

    except ValueError as ve:
        await message.reply_text(str(ve))
    except Exception as e:
        logger.exception("Error in give_character_command")
        await message.reply_text("❌ An unexpected error occurred while giving the character.")


# -------------------- /add -------------------- #
async def add_all_characters_for_user(user_id: int) -> str:
    """
    Adds all characters from global collection to user's characters array (only new ones).
    Returns summary string.
    """
    # fetch all chars (only required fields)
    all_chars = await collection.find({}, projection={'_id': 0, 'id': 1, 'name': 1, 'anime': 1, 'rarity': 1, 'img_url': 1}).to_list(length=None)
    if not all_chars:
        return "⚠️ No characters found in the database."

    # ensure user doc and get current count
    await _ensure_user_doc(user_id)
    user_doc = await user_collection.find_one({'id': user_id}, projection={'_id': 0, 'characters': 1})
    current = user_doc.get('characters') or []
    current_ids = {c['id'] for c in current}

    # prepare only new characters
    new_chars = [c for c in all_chars if c['id'] not in current_ids]
    if not new_chars:
        return f"ℹ️ No new characters to add for user <code>{user_id}</code>."

    # push new chars
    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': {'$each': new_chars}}}
    )

    return f"✅ Added {len(new_chars)} new characters to user <code>{user_id}</code>."


@app.on_message(filters.command("add"))
async def add_characters_command(client, message: Message):
    sender_id = message.from_user.id
    if sender_id not in DEV_LIST:
        await message.reply_text("⛔ You are not authorized to use this command.")
        return

    # Optional argument: /add <target_user_id>
    parts = message.text.split()
    if len(parts) >= 2:
        try:
            target_user_id = int(parts[1])
        except ValueError:
            await message.reply_text("❌ Invalid user id. Usage: /add [user_id]")
            return
    else:
        target_user_id = message.from_user.id

    try:
        result_msg = await add_all_characters_for_user(target_user_id)
        await message.reply_text(result_msg, parse_mode='html')
    except Exception as e:
        logger.exception("Error in add_characters_command")
        await message.reply_text("❌ An error occurred while adding characters.")


# -------------------- /kill -------------------- #
async def kill_character(receiver_id: int, character_id: str) -> str:
    """Remove a character by id from a user's characters array."""
    # ensure doc exists
    await _ensure_user_doc(receiver_id)

    res = await user_collection.update_one(
        {'id': receiver_id},
        {'$pull': {'characters': {'id': character_id}}}
    )

    if res.modified_count == 0:
        raise ValueError("⚠️ Character was not present in user's collection.")
    return f"🗑️ Removed character <code>{character_id}</code> from user <code>{receiver_id}</code>."


@app.on_message(filters.command("kill") & filters.reply)
async def remove_character_command(client, message: Message):
    sender_id = message.from_user.id
    if sender_id not in DEV_LIST:
        await message.reply_text("⛔ You are not authorized to use this command.")
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply_text("⚠️ Reply to a user's message to remove a character from them.")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.reply_text("❌ Usage: /kill <character_id>  (reply to target user's message)")
        return

    char_id = parts[1].strip()
    receiver_id = message.reply_to_message.from_user.id

    try:
        out = await kill_character(receiver_id, char_id)
        await message.reply_text(out, parse_mode='html')
    except ValueError as ve:
        await message.reply_text(str(ve))
    except Exception:
        logger.exception("Error in remove_character_command")
        await message.reply_text("❌ An unexpected error occurred while removing the character.")