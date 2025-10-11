import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from Grabber import (
    collection, 
    top_global_groups_collection, 
    group_user_totals_collection, 
    user_collection, 
    user_totals_collection, 
    shivuu,
    application, 
    SUPPORT_CHAT, 
    UPDATE_CHAT, 
    db, 
    LOGGER
)
from Grabber.modules import ALL_MODULES

# Global state dictionaries
locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
last_user = {}
warned_users = {}

# Import all modules
for module_name in ALL_MODULES:
    try:
        imported_module = importlib.import_module("Grabber.modules." + module_name)
        LOGGER.info(f"Successfully imported module: {module_name}")
    except Exception as e:
        LOGGER.error(f"Failed to import module {module_name}: {e}")


def escape_markdown(text):
    """Escape markdown special characters"""
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', str(text))


async def message_counter(update: Update, context: CallbackContext) -> None:
    """Count messages and trigger character spawn"""
    try:
        # Ignore updates without user info
        if not update.effective_user or not update.effective_chat or not update.message:
            return

        chat_id = str(update.effective_chat.id)
        user_id = update.effective_user.id

        # Initialize lock for this chat
        if chat_id not in locks:
            locks[chat_id] = asyncio.Lock()
        lock = locks[chat_id]

        async with lock:
            # Get message frequency for this chat
            chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
            message_frequency = chat_frequency.get('message_frequency', 100) if chat_frequency else 100

            # Check for spam (same user sending many messages in a row)
            current_time = time.time()
            if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
                last_user[chat_id]['count'] += 1
                
                if last_user[chat_id]['count'] >= 10:
                    # Check if user was recently warned
                    if user_id in warned_users and current_time - warned_users[user_id] < 600:
                        return
                    else:
                        await update.message.reply_text(
                            f"⚠️ Don't Spam {update.effective_user.first_name}...\n"
                            f"Your messages will be ignored for 10 minutes..."
                        )
                        warned_users[user_id] = current_time
                        return
            else:
                last_user[chat_id] = {'user_id': user_id, 'count': 1}

            # Increment message count
            message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

            # Check if it's time to spawn a character
            if message_counts[chat_id] % message_frequency == 0:
                await send_image(update, context)
                message_counts[chat_id] = 0
                
    except Exception as e:
        LOGGER.error(f"Error in message_counter: {e}")


async def send_image(update: Update, context: CallbackContext) -> None:
    """Send a random character image to the chat"""
    try:
        chat_id = update.effective_chat.id
        
        # Fetch all characters from database
        all_characters = await collection.find({}).to_list(length=None)

        if not all_characters:
            await update.message.reply_text("⚠️ No characters found in the database.")
            return

        # Initialize sent characters list for this chat
        if chat_id not in sent_characters:
            sent_characters[chat_id] = []

        # Reset if all characters have been sent
        if len(sent_characters[chat_id]) >= len(all_characters):
            sent_characters[chat_id] = []

        # Get available characters (not yet sent in this chat)
        available = [c for c in all_characters if c.get("id") not in sent_characters[chat_id]]
        
        if not available:
            # Fallback: use all characters if none available
            available = all_characters
            sent_characters[chat_id] = []

        # Pick a random character
        character = random.choice(available)
        sent_characters[chat_id].append(character.get("id"))
        last_characters[chat_id] = character

        # Reset first correct guess for this chat
        if chat_id in first_correct_guesses:
            del first_correct_guesses[chat_id]

        # Try to get image URL from various possible fields
        img_url = (
            character.get("img_url") or
            character.get("image") or
            character.get("url") or
            character.get("photo") or
            character.get("img") or
            character.get("thumbnail")
        )

        if not img_url:
            LOGGER.warning(f"No image URL found for character: {character.get('name', 'Unknown')}")
            await update.message.reply_text("⚠️ Character image not available.")
            return

        # Prepare caption
        caption = (
            f"🎭 A new *{character.get('rarity', 'Unknown')}* character appeared!\n\n"
            f"Guess their name using `/guess <name>` to add them to your harem!"
        )

        # Send character image
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=img_url,
            caption=caption,
            parse_mode="Markdown",
        )
        
        LOGGER.info(f"[✅ SENT] Character: {character.get('name', 'Unknown')} | Chat: {chat_id}")
        
    except Exception as e:
        LOGGER.error(f"[❌ ERROR] Failed to send character: {e}")
        try:
            await update.message.reply_text(f"❌ Failed to send character. Please try again later.")
        except:
            pass


async def guess(update: Update, context: CallbackContext) -> None:
    """Handle character name guessing"""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        # Check if there's a character to guess
        if chat_id not in last_characters:
            await update.message.reply_text("❌ No character to guess right now. Wait for one to appear!")
            return

        # Check if someone already guessed correctly
        if chat_id in first_correct_guesses:
            await update.message.reply_text(f'❌ Already guessed by someone. Try next time!')
            return

        # Get user's guess
        guess = ' '.join(context.args).lower().strip() if context.args else ''
        
        if not guess:
            await update.message.reply_text("❌ Please provide a character name. Usage: `/guess <name>`", parse_mode="Markdown")
            return

        # Check for invalid characters in guess
        if "()" in guess or "&" in guess:
            await update.message.reply_text("❌ You can't use special characters like () or & in your guess.")
            return

        # Get the correct character name
        character = last_characters[chat_id]
        correct_name = character.get('name', '').lower().strip()
        name_parts = correct_name.split()

        # Check if guess matches the character name
        guess_parts = guess.split()
        is_correct = (
            sorted(name_parts) == sorted(guess_parts) or  # Full name in any order
            guess == correct_name or  # Exact match
            any(part == guess for part in name_parts)  # Single name part match
        )

        if is_correct:
            # Mark as correctly guessed
            first_correct_guesses[chat_id] = user_id

            # Update or create user document
            user = await user_collection.find_one({'id': user_id})
            
            if user:
                # Update user info if changed
                update_fields = {}
                if hasattr(update.effective_user, 'username') and update.effective_user.username:
                    if update.effective_user.username != user.get('username'):
                        update_fields['username'] = update.effective_user.username
                if update.effective_user.first_name != user.get('first_name'):
                    update_fields['first_name'] = update.effective_user.first_name
                
                if update_fields:
                    await user_collection.update_one({'id': user_id}, {'$set': update_fields})

                # Add character to user's collection
                await user_collection.update_one(
                    {'id': user_id}, 
                    {'$push': {'characters': character}}
                )
            else:
                # Create new user
                await user_collection.insert_one({
                    'id': user_id,
                    'username': getattr(update.effective_user, 'username', None),
                    'first_name': update.effective_user.first_name,
                    'characters': [character],
                })

            # Update group user totals
            group_user_total = await group_user_totals_collection.find_one({
                'user_id': user_id, 
                'group_id': chat_id
            })
            
            if group_user_total:
                # Update user info if changed
                update_fields = {}
                if hasattr(update.effective_user, 'username') and update.effective_user.username:
                    if update.effective_user.username != group_user_total.get('username'):
                        update_fields['username'] = update.effective_user.username
                if update.effective_user.first_name != group_user_total.get('first_name'):
                    update_fields['first_name'] = update.effective_user.first_name
                
                if update_fields:
                    await group_user_totals_collection.update_one(
                        {'user_id': user_id, 'group_id': chat_id}, 
                        {'$set': update_fields}
                    )

                # Increment count
                await group_user_totals_collection.update_one(
                    {'user_id': user_id, 'group_id': chat_id}, 
                    {'$inc': {'count': 1}}
                )
            else:
                # Create new group user total
                await group_user_totals_collection.insert_one({
                    'user_id': user_id,
                    'group_id': chat_id,
                    'username': getattr(update.effective_user, 'username', None),
                    'first_name': update.effective_user.first_name,
                    'count': 1,
                })

            # Update global group stats
            group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
            
            if group_info:
                # Update group name if changed
                if update.effective_chat.title != group_info.get('group_name'):
                    await top_global_groups_collection.update_one(
                        {'group_id': chat_id}, 
                        {'$set': {'group_name': update.effective_chat.title}}
                    )

                # Increment count
                await top_global_groups_collection.update_one(
                    {'group_id': chat_id}, 
                    {'$inc': {'count': 1}}
                )
            else:
                # Create new group
                await top_global_groups_collection.insert_one({
                    'group_id': chat_id,
                    'group_name': update.effective_chat.title,
                    'count': 1,
                })

            # Create inline keyboard for harem
            keyboard = [[
                InlineKeyboardButton(
                    "📋 See Harem", 
                    switch_inline_query_current_chat=f"collection.{user_id}"
                )
            ]]

            # Send success message
            response = (
                f'✅ <b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> '
                f'guessed correctly!\n\n'
                f'📛 <b>NAME:</b> {escape(character["name"])}\n'
                f'🎬 <b>ANIME:</b> {escape(character.get("anime", "Unknown"))}\n'
                f'⭐ <b>RARITY:</b> {escape(character.get("rarity", "Unknown"))}\n\n'
                f'This character has been added to your harem! Use /harem to see your collection.'
            )

            await update.message.reply_text(
                response,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            LOGGER.info(f"User {user_id} correctly guessed {character.get('name')} in chat {chat_id}")
            
        else:
            await update.message.reply_text('❌ Wrong guess! Try again with the correct character name.')
            
    except Exception as e:
        LOGGER.error(f"Error in guess command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")


async def fav(update: Update, context: CallbackContext) -> None:
    """Set a favorite character"""
    try:
        user_id = update.effective_user.id

        # Check if character ID was provided
        if not context.args:
            await update.message.reply_text('❌ Please provide a character ID.\nUsage: `/fav <character_id>`', parse_mode="Markdown")
            return

        character_id = context.args[0]

        # Get user from database
        user = await user_collection.find_one({'id': user_id})
        
        if not user:
            await update.message.reply_text('❌ You have not guessed any characters yet.')
            return

        # Check if user has this character
        character = next(
            (c for c in user.get('characters', []) if c.get('id') == character_id), 
            None
        )
        
        if not character:
            await update.message.reply_text('❌ This character is not in your collection.')
            return

        # Set as favorite (replacing any existing favorite)
        await user_collection.update_one(
            {'id': user_id}, 
            {'$set': {'favorites': [character_id]}}
        )

        await update.message.reply_text(
            f'⭐ Character **{character.get("name", "Unknown")}** has been set as your favorite!',
            parse_mode="Markdown"
        )
        
        LOGGER.info(f"User {user_id} set {character.get('name')} as favorite")
        
    except Exception as e:
        LOGGER.error(f"Error in fav command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")


def main() -> None:
    """Run the bot"""
    try:
        # Add command handlers
        application.add_handler(
            CommandHandler(
                ["guess", "protecc", "collect", "grab", "hunt"], 
                guess, 
                block=False
            )
        )
        application.add_handler(CommandHandler("fav", fav, block=False))
        
        # Add message handler for counting
        application.add_handler(
            MessageHandler(
                filters.ALL, 
                message_counter, 
                block=False
            )
        )

        LOGGER.info("Starting bot polling...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        LOGGER.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    try:
        shivuu.start()
        LOGGER.info("✅ Bot started successfully")
        main()
    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user")
    except Exception as e:
        LOGGER.error(f"Fatal error: {e}")
        raise