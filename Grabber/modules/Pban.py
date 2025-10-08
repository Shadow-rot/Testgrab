from pyrogram import filters, Client, types as t
from Grabber import shivuu as bot
from telegram.ext import CommandHandler, CallbackContext
from Grabber import user_collection, collection
from datetime import datetime, timedelta

SUDO_USERS = (5116239739)  # Sudo users who can bypass bans

# Dictionary to store ban information
ban_info = {}

# Function to check if a user is banned
def is_banned(user_id):
    if user_id in SUDO_USERS:
        return False
    if user_id in ban_info:
        ban_details = ban_info[user_id]
        if ban_details['end_time'] is None or ban_details['end_time'] > datetime.now():
            return True
    return False

# Function to ban a user
def ban_user(user_id, duration=None):
    if duration:
        end_time = datetime.now() + timedelta(days=duration)
    else:
        end_time = None  # Permanent ban
    ban_info[user_id] = {'end_time': end_time}

# Command to ban a user
@bot.on_message(filters.command(["pban"]))
async def pban(_, message: t.Message):
    if message.from_user.id not in SUDO_USERS:
        return await message.reply_text("You do not have permission to use this command.", quote=True)

    if len(message.command) < 3:
        return await message.reply_text("Please provide the user ID or username and ban duration (in days, or 'perm' for permanent ban).", quote=True)

    try:
        user_id = int(message.command[1])
    except ValueError:
        try:
            user = await bot.get_users(message.command[1])
            user_id = user.id
        except Exception as e:
            return await message.reply_text("Invalid user ID or username.", quote=True)

    duration = message.command[2]

    if duration.lower() == 'perm':
        ban_user(user_id)
        await message.reply_text(f"User {user_id} has been permanently banned.", quote=True)
    else:
        try:
            duration = int(duration)
            ban_user(user_id, duration)
            await message.reply_text(f"User {user_id} has been banned for {duration} days.", quote=True)
        except ValueError:
            await message.reply_text("Invalid duration. Please provide a number of days or 'perm'.", quote=True)

# Command to unban a user
@bot.on_message(filters.command(["punban"]))
async def punban(_, message: t.Message):
    if message.from_user.id not in SUDO_USERS:
        return await message.reply_text("You do not have permission to use this command.", quote=True)

    if len(message.command) < 2:
        return await message.reply_text("Please provide the user ID or username.", quote=True)

    try:
        user_id = int(message.command[1])
    except ValueError:
        try:
            user = await bot.get_users(message.command[1])
            user_id = user.id
        except Exception as e:
            return await message.reply_text("Invalid user ID or username.", quote=True)

    if user_id in ban_info:
        del ban_info[user_id]
        await message.reply_text(f"User {user_id} has been unbanned.", quote=True)
    else:
        await message.reply_text(f"User {user_id} is not banned.", quote=True)

# Middleware to check for banned users on commands only
@bot.on_message(filters.command)
async def check_ban(client: Client, message: t.Message):
    user_id = message.from_user.id
    if is_banned(user_id):
        ban_details = ban_info[user_id]
        end_time = ban_details['end_time']
        if end_time:
            ban_end = end_time.strftime("%Y-%m-%d %H:%M:%S")
            await message.reply_text(f"You are banned from using commands until {ban_end}. Appeal at @naruto_support1", quote=True)
        else:
            await message.reply_text("You are permanently banned from using commands. Appeal at @naruto_support1", quote=True)
        return False  # Prevent the command from being processed
    return True  # Allow the comm
PERMANENTBAN_HANDLER= CommandHandler('Pban', pban, block=False)
