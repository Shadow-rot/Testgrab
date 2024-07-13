from pyrogram import Client
from shivu.Database.db import get_user_data

def get_inventory(user_id):
    user_data = get_user_data(user_id)
    if not user_data:
        return None

    inventory = {
        "first_name": user_data.get("first_name"),
        "user_id": user_id,
        "yen": user_data.get("yen", 0),
        "ruby": user_data.get("ruby", 0),
        "level": user_data.get("stats", {}).get("Level", 1),
        "experience": user_data.get("stats", {}).get("Experience", 0),
    }
    return inventory

async def inventory_command(client, message):
    user_id = str(message.from_user.id)
    inventory = get_inventory(user_id)

    if not inventory:
        await message.reply("No inventory found. Please start the bot to check ur inventory first.")
        return

    inventory_message = (
        f"🤵Name: {message.from_user.first_name}\n"
        f"🆔User Id: {inventory['user_id']}\n"
        f"💰Yen: {inventory['yen']}\n"
        f"💎Ruby: {inventory['ruby']}\n"
        f"🎚️Level: {inventory['level']}\n"
        f"✨Experience: {inventory['experience']}\n"
    )

    await message.reply(inventory_message, reply_markup=keyboard)
