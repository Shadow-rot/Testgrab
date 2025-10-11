import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import MongoClient, ASCENDING

from telegram import Update, InlineQueryResultPhoto
from telegram.ext import InlineQueryHandler, CallbackContext, CommandHandler 
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from Grabber import user_collection, collection, application, db, LOGGER


# collection
db.characters.create_index([('id', ASCENDING)])
db.characters.create_index([('anime', ASCENDING)])
db.characters.create_index([('img_url', ASCENDING)])

# user_collection
db.user_collection.create_index([('characters.id', ASCENDING)])
db.user_collection.create_index([('characters.name', ASCENDING)])
db.user_collection.create_index([('characters.img_url', ASCENDING)])

all_characters_cache = TTLCache(maxsize=10000, ttl=36000)
user_collection_cache = TTLCache(maxsize=10000, ttl=60)


def get_image_url(character):
    """Get image URL from character with multiple fallback options"""
    return (
        character.get('img_url') or
        character.get('image') or
        character.get('url') or
        character.get('photo') or
        character.get('img') or
        character.get('thumbnail') or
        'https://via.placeholder.com/500x700.png?text=No+Image'  # Fallback placeholder
    )


async def inlinequery(update: Update, context: CallbackContext) -> None:
    try:
        query = update.inline_query.query
        offset = int(update.inline_query.offset) if update.inline_query.offset else 0

        if query.startswith('collection.'):
            # Parse user collection query
            parts = query.split(' ')
            user_id = parts[0].split('.')[1] if '.' in parts[0] else None
            search_terms = ' '.join(parts[1:]) if len(parts) > 1 else ''
            
            if user_id and user_id.isdigit():
                # Check cache first
                if user_id in user_collection_cache:
                    user = user_collection_cache[user_id]
                else:
                    user = await user_collection.find_one({'id': int(user_id)})
                    if user:
                        user_collection_cache[user_id] = user

                if user and user.get('characters'):
                    # Remove duplicates by id
                    all_characters = list({v['id']: v for v in user['characters']}.values())
                    
                    # Apply search filter if provided
                    if search_terms:
                        regex = re.compile(search_terms, re.IGNORECASE)
                        all_characters = [
                            character for character in all_characters 
                            if regex.search(character.get('name', '')) or regex.search(character.get('anime', ''))
                        ]
                else:
                    all_characters = []
            else:
                all_characters = []
        else:
            # Global character search
            if query:
                regex = re.compile(query, re.IGNORECASE)
                cursor = collection.find({"$or": [{"name": regex}, {"anime": regex}]})
                all_characters = await cursor.to_list(length=None)
            else:
                # Get all characters (with caching)
                if 'all_characters' in all_characters_cache:
                    all_characters = all_characters_cache['all_characters']
                else:
                    cursor = collection.find({})
                    all_characters = await cursor.to_list(length=None)
                    all_characters_cache['all_characters'] = all_characters

        # Pagination
        characters = all_characters[offset:offset + 50]
        if len(all_characters) > offset + 50:
            next_offset = str(offset + 50)
        else:
            next_offset = ''

        results = []
        for character in characters:
            try:
                # Get image URL with fallback
                img_url = get_image_url(character)
                
                # Get global count
                global_count = await user_collection.count_documents({'characters.id': character.get('id')})
                
                # Get anime character count
                anime_characters = await collection.count_documents({'anime': character.get('anime')})

                if query.startswith('collection.'):
                    # User collection caption
                    user_character_count = sum(1 for c in user.get('characters', []) if c.get('id') == character.get('id'))
                    user_anime_characters = sum(1 for c in user.get('characters', []) if c.get('anime') == character.get('anime'))
                    
                    caption = (
                        f"<b>Look At <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', str(user['id'])))}</a>'s Character</b>\n\n"
                        f"🌸: <b>{escape(character.get('name', 'Unknown'))} (x{user_character_count})</b>\n"
                        f"🏖️: <b>{escape(character.get('anime', 'Unknown'))} ({user_anime_characters}/{anime_characters})</b>\n"
                        f"<b>{escape(character.get('rarity', 'Unknown'))}</b>\n\n"
                        f"<b>🆔️:</b> {character.get('id', 'N/A')}"
                    )
                else:
                    # Global search caption
                    caption = (
                        f"<b>Look At This Character !!</b>\n\n"
                        f"🌸: <b>{escape(character.get('name', 'Unknown'))}</b>\n"
                        f"🏖️: <b>{escape(character.get('anime', 'Unknown'))}</b>\n"
                        f"<b>{escape(character.get('rarity', 'Unknown'))}</b>\n"
                        f"🆔️: <b>{character.get('id', 'N/A')}</b>\n\n"
                        f"<b>Globally Guessed {global_count} Times...</b>"
                    )
                
                results.append(
                    InlineQueryResultPhoto(
                        id=f"{character.get('id', 'unknown')}_{time.time()}",
                        photo_url=img_url,
                        thumbnail_url=img_url,
                        caption=caption,
                        parse_mode='HTML'
                    )
                )
            except Exception as char_error:
                LOGGER.error(f"Error processing character {character.get('id', 'unknown')}: {char_error}")
                continue

        await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)
        
    except Exception as e:
        LOGGER.error(f"Error in inline query: {e}", exc_info=True)
        # Send empty result on error
        try:
            await update.inline_query.answer([])
        except:
            pass


application.add_handler(InlineQueryHandler(inlinequery, block=False))