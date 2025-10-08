import io
import os
import logging
import aiohttp
import mimetypes
import urllib.parse

from pymongo import ReturnDocument
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.error import TelegramError

from Grabber import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

logger = logging.getLogger(__name__)

RARITY_MAP = {
    1: "⚪ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",
    4: "🟢 Medium",
    5: "💮 Limited",
    6: "🧬 X-verse"
}

USAGE = """❌ Wrong format!
Via URL:
  /upload <url> <character-name> <anime-name> <rarity>
Reply to media:
  Reply to a photo/video/document -> /upload <character-name> <anime-name> <rarity>

Use dashes for multiword names (they become spaces).
Rarity: 1..6
"""

MAX_BYTES = 50 * 1024 * 1024  # 50 MB


async def get_next_sequence_number(sequence_name: str) -> int:
    seq_collection = db.sequences
    seq_doc = await seq_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(seq_doc['sequence_value'])


def nice_title(raw: str) -> str:
    return raw.replace('-', ' ').strip().title()


async def download_url_to_bytes(url: str, timeout: int = 30) -> tuple[bytes, str]:
    """
    Download url and return (bytes, content_type).
    Raises Exception on non-200 or too large.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (compatible)'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
            if resp.status != 200:
                raise ValueError(f"HTTP {resp.status}")
            content_length = resp.headers.get('Content-Length')
            if content_length and int(content_length) > MAX_BYTES:
                raise ValueError("File too large")
            data = await resp.read()
            if len(data) > MAX_BYTES:
                raise ValueError("File too large")
            ctype = (resp.headers.get('Content-Type') or '').split(';')[0].lower()
            return data, ctype


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message

    if str(user.id) not in sudo_users:
        await msg.reply_text("⚠️ Ask my Sensei for permission.")
        return

    args = context.args or []
    reply = msg.reply_to_message

    try:
        # --------------- REPLY-TO-MEDIA flow ---------------
        if reply and len(args) == 3:
            # usage: reply -> /upload char-name anime-name rarity
            char_name = nice_title(args[0])
            anime_name = nice_title(args[1])
            try:
                rarity_text = RARITY_MAP[int(args[2])]
            except (ValueError, KeyError):
                await msg.reply_text("❌ Invalid rarity. Use 1..6.")
                return

            # decide file_id and file_kind
            file_id = None
            file_kind = None
            mime = None

            if reply.photo:
                file_id = reply.photo[-1].file_id
                file_kind = 'photo'
            elif reply.animation:
                file_id = reply.animation.file_id
                file_kind = 'animation'
            elif reply.video:
                file_id = reply.video.file_id
                file_kind = 'video'
            elif reply.document:
                file_id = reply.document.file_id
                file_kind = 'document'
                mime = reply.document.mime_type
            elif reply.audio:
                file_id = reply.audio.file_id
                file_kind = 'audio'
            elif reply.voice:
                file_id = reply.voice.file_id
                file_kind = 'voice'
            else:
                await msg.reply_text("⚠️ Reply must be photo/video/animation/document/audio/voice.")
                return

            char_id = str(await get_next_sequence_number("character_id")).zfill(3)
            doc = {
                "file_ref": file_id,
                "is_file_id": True,
                "file_type": mime or file_kind,
                "name": char_name,
                "anime": anime_name,
                "rarity": rarity_text,
                "id": char_id
            }

            # send to channel using file_id (fast)
            try:
                caption = (
                    f"<b>Character Name:</b> {char_name}\n"
                    f"<b>Anime Name:</b> {anime_name}\n"
                    f"<b>Rarity:</b> {rarity_text}\n"
                    f"<b>ID:</b> {char_id}\n"
                    f"Added by <a href='tg://user?id={user.id}'>{user.first_name}</a>"
                )

                if file_kind == 'photo':
                    sent = await context.bot.send_photo(chat_id=CHARA_CHANNEL_ID, photo=file_id, caption=caption, parse_mode='HTML')
                elif file_kind == 'video':
                    sent = await context.bot.send_video(chat_id=CHARA_CHANNEL_ID, video=file_id, caption=caption, parse_mode='HTML')
                elif file_kind == 'animation':
                    sent = await context.bot.send_animation(chat_id=CHARA_CHANNEL_ID, animation=file_id, caption=caption, parse_mode='HTML')
                elif file_kind in ('audio', 'voice'):
                    # send as document to preserve file
                    sent = await context.bot.send_document(chat_id=CHARA_CHANNEL_ID, document=file_id, caption=caption, parse_mode='HTML')
                else:
                    sent = await context.bot.send_document(chat_id=CHARA_CHANNEL_ID, document=file_id, caption=caption, parse_mode='HTML')

                doc['message_id'] = sent.message_id
                await collection.insert_one(doc)
                await msg.reply_text(f"✅ Character added (ID: {char_id}). Posted to channel.")
                return

            except TelegramError as e:
                # fallback: store in DB without message_id to avoid data loss
                await collection.insert_one(doc)
                logger.exception("Failed to post reply media to channel")
                await msg.reply_text(f"⚠️ Saved to DB but failed to post to channel: {e}")
                return

        # --------------- URL flow ---------------
        elif len(args) == 4:
            url = args[0].strip()
            char_name = nice_title(args[1])
            anime_name = nice_title(args[2])
            try:
                rarity_text = RARITY_MAP[int(args[3])]
            except (ValueError, KeyError):
                await msg.reply_text("❌ Invalid rarity. Use 1..6.")
                return

            # basic scheme check
            if not (url.startswith("http://") or url.startswith("https://")):
                await msg.reply_text("❌ URL must start with http:// or https://")
                return

            # download bytes (works for catbox/imgur/telegraph)
            try:
                data, content_type = await download_url_to_bytes(url)
            except Exception as e:
                logger.exception("download_url_to_bytes failed")
                await msg.reply_text(f"❌ Could not download file: {e}")
                return

            # small safety check
            if not data:
                await msg.reply_text("❌ Empty file or failed to download.")
                return

            char_id = str(await get_next_sequence_number("character_id")).zfill(3)

            # guess filename from url or fallback
            parsed = urllib.parse.urlparse(url)
            fname = os.path.basename(parsed.path) or f"file_{char_id}"
            if not os.path.splitext(fname)[1]:
                # try extension from content_type
                ext = mimetypes.guess_extension(content_type or '') or ''
                fname = fname + ext

            fileio = io.BytesIO(data)
            fileio.name = fname
            fileio.seek(0)

            caption = (
                f"<b>Character Name:</b> {char_name}\n"
                f"<b>Anime Name:</b> {anime_name}\n"
                f"<b>Rarity:</b> {rarity_text}\n"
                f"<b>ID:</b> {char_id}\n"
                f"Added by <a href='tg://user?id={user.id}'>{user.first_name}</a>"
            )

            doc = {
                "file_ref": url,
                "is_file_id": False,
                "file_type": content_type or 'unknown',
                "name": char_name,
                "anime": anime_name,
                "rarity": rarity_text,
                "id": char_id
            }

            # try best-suited send method
            try:
                if content_type and content_type.startswith('image'):
                    sent = await context.bot.send_photo(chat_id=CHARA_CHANNEL_ID, photo=fileio, caption=caption, parse_mode='HTML')
                elif content_type and content_type.startswith('video'):
                    sent = await context.bot.send_video(chat_id=CHARA_CHANNEL_ID, video=fileio, caption=caption, parse_mode='HTML')
                else:
                    # fallback to send_document (safe for any file)
                    # rewind before sending
                    fileio.seek(0)
                    sent = await context.bot.send_document(chat_id=CHARA_CHANNEL_ID, document=fileio, caption=caption, parse_mode='HTML')

                doc['message_id'] = sent.message_id
                await collection.insert_one(doc)
                await msg.reply_text(f"✅ Character added (ID: {char_id}). Posted to channel.")
                fileio.close()
                return

            except TelegramError as e:
                logger.exception("Failed to post downloaded url to channel")
                # still store DB entry without message_id
                await collection.insert_one(doc)
                await msg.reply_text(f"⚠️ Saved to DB but failed to post to channel: {e}")
                fileio.close()
                return

        else:
            await msg.reply_text(USAGE)
            return

    except Exception as exc:
        logger.exception("Upload command error")
        await msg.reply_text(f"❌ Upload failed: {exc}\nIf problem persists contact: {SUPPORT_CHAT}")
        return


UPLOAD_HANDLER = CommandHandler("upload", upload, block=False)
application.add_handler(UPLOAD_HANDLER)