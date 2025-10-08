from telegram import Update
from telegram.ext import CommandHandler
import random
import asyncio
from Grabber import application, user_collection

# Dictionary to store user's items
user_data = {
    'Sword': 36,
    'Choco': 15,
    'exp': 10  # Initial exp set to 10
}

# List of monster names
monster_names = [
    "Goblin", "Orc", "Troll", "Dragon", "Skeleton", "Witch", "Vampire", "Werewolf",
    "Cyclops", "Minotaur", "Banshee", "Ghost", "Zombie", "Specter", "Manticore",
    "Hydra", "Siren", "Basilisk", "Chimera", "Kraken", "Phoenix", "Yeti", "Griffin",
    "Cerberus", "Harpy", "Wendigo", "Behemoth", "Cthulhu", "Medusa", "Gorgon",
    "Necromancer", "Warlock", "Lich", "Demon", "Djinn", "Fairy"
]

# Command handler for /sbag
async def sbag(update: Update, context):
    if user_data['exp'] >= 10:
        item_list_message = "Your Item List:\n"
        for item, quantity in user_data.items():
            item_list_message += f"ðŸ—¡ {item}: {quantity}\n"
        await update.message.reply_text(item_list_message)
    else:
        await update.message.reply_text("You don't have enough exp to see sbag.")

# Command handler for /shunt
async def shunt(update: Update, context):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if the user is on cooldown
    if user_id in last_shunt_time:
        time_since_last_shunt = current_time - last_shunt_time[user_id]
        cooldown_remaining = timedelta(seconds=30) - time_since_last_shunt
        if cooldown_remaining > timedelta(seconds=0):
            await update.message.reply_text(f"Please wait {cooldown_remaining.seconds} seconds before using shunt again.")
            return

# Command handler for /shunt
async def shunt(update: Update, context):
    user_id = update.effective_user.id
    current_time = datetime.now()

    # Check if the user is on cooldown
    if user_id in last_shunt_time:
        time_since_last_shunt = current_time - last_shunt_time[user_id]
        cooldown_remaining = timedelta(seconds=30) - time_since_last_shunt
        if cooldown_remaining > timedelta(seconds=0):
            await update.message.reply_text(f"Please wait {cooldown_remaining.seconds} seconds before using shunt again.")
            return
async def shunt(update: Update, context):
    monster_name = random.choice(monster_names)
    rank = random.choice(['F', 'E', 'D', 'C', 'B', 'A', 'S'])
    event = f"You found an [ {rank} ] Rank {monster_name} Dungeon."
    if 'F' in event:
        result_message = "You lostðŸ’€.\nAnd Goblin Fucked your BeastðŸ’€."
    else:
        won_tokens = random.randint(1000, 10000)
        user_data['exp'] += random.randint(10, 30)  # Adding random exp between 10 to 30
        result_message = f"You won the fight! You got these items:\n\nGold: {won_tokens}"
    await update.message.reply_text(
        f"Ë¹pick\n\n{event}\n\n{result_message}"
    )


async def xp(update, context):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id})
    user_balance = 100
    amount = 50
    if user_balance < amount:
       print("You don't have enough!")
    user_balance = user_data.get('balance', 0)  
    # Coin landing randomly on head or tail
    coin_landing = random.choice(["H", "T"])
    if choice == coin_landing:
        won_amount = 2 * amount
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': won_amount}})
        message = f"You chose {'Head' if choice == 'H' else 'Tail'} and won Ŧ{won_amount:,.0f}.\nCoin landed on {coin_landing}."
    else:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -amount}})
        message = f"You chose {'Head' if choice == 'H' else 'Tail'} and lost Ŧ{amount:,.0f}.\nCoin landed on {coin_landing}."

    await update.message.reply_text(message)
    await update.message.reply_photo(
        photo='https://graph.org/file/67e87de8ab7ed5ce6d57f.jpg',
        caption="Here is the coin toss result."
    )
