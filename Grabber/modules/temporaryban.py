import asyncio
from pyrogram import filters, Client, types as t
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shivu import shivuu as bot
from shivu import user_collection, collection
from datetime import datetime, timedelta
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

def get_chat_id(bot, chat_name):
    """Gets the chat ID of a Telegram chat by its name."""
    chat = bot.get_chat(chat_name)
    return chat.id

def get_user_id(bot, user_name):
    """Gets the user ID of a Telegram user by their name."""
    user = bot.get_user(user_name)
    return user.id

def ban_user(bot, chat_id, user_id, duration):
    """Bans a user from a Telegram chat for a given duration."""
    bot.kick_chat_member(chat_id, user_id, reason="Spam")
    bot.unban_chat_member(chat_id, user_id, until_date=datetime.datetime.now() + timedelta(minutes=duration))

def main():
    """The main function."""
    bot = telegram.Bot(token="YOUR_BOT_TOKEN")

    # Get the chat ID of the group.
    chat_id = get_chat_id(bot, "YOUR_GROUP_NAME")

    # Get the user ID of the user to ban.
    user_id = get_user_id(bot, "YOUR_USER_NAME")

    # Ban the user for 10 minutes.
    ban_user(bot, chat_id, user_id, 10)
