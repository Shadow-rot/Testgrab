from telegram.ext import CommandHandler
from shivu import application, user_collection
from telegram import Update
from datetime import datetime, timedelta
import asyncio
import math

# Dictionary to store last payment times
last_payment_times = {}

last_loan_times = {}

async def balance(update, context):
    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'saved_amount': 1, 'loan_amount': 1, 'potion_amount': 1, 'potion_expiry': 1})

    if user_data:
        balance_amount = user_data.get('balance',0)
        saved_amount = user_data.get('saved_amount', 0)
        loan_amount = user_data.get('loan_amount', 0)
        potion_amount = user_data.get('potion_amount', 0)
        potion_expiry = user_data.get('potion_expiry')

        formatted_balance = "Ŧ{:,.0f}``".format(balance_amount)
        formatted_saved = "Ŧ{:,.0f}``".format(saved_amount)
        formatted_loan = "Ŧ{:,.0f}``".format(loan_amount)

        balance_message = f"Your current balance is: {formatted_balance}\n"
        balance_message += f"Amount saved: {formatted_saved}\n"
        balance_message += f"Loan amount: {formatted_loan}\n"
        balance_message += f"Potion amount: {potion_amount}\n"

        if potion_expiry:
            time_remaining = potion_expiry - datetime.now()
            balance_message += f"Potion time remaining: {time_remaining}\n"

        await update.message.reply_text(balance_message)
    else:
        balance_message = "You haven't added any character yet. First add a character to unlock all features."
        await update.message.reply_text(balance_message)

async def save(update, context):
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Please provide a positive integer.")
        return

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1})

    if user_data:
        balance_amount = user_data.get('balance', 0)

        if amount > balance_amount:
            await update.message.reply_text("Insufficient balance to save this amount.")
            return

        new_balance = balance_amount - amount

        # Update user balance and saved amount
        await user_collection.update_one({'id': user_id}, {'$set': {'balance': new_balance}, '$inc': {'saved_amount': amount}})

        await update.message.reply_text(f"You saved Ŧ{amount} in your bank account.")
    else:
        await update.message.reply_text("User data not found.")


async def withdraw(update, context):
    try:
        amount = int(context.args[0])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if amount > 1182581151717:  # Set the withdrawal limit here
            await update.message.reply_text("Withdrawal amount exceeds the limit is 1182581151717.")
            return
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid amount. Please provide a positive integer.")
        return

    

    user_id = update.effective_user.id
    user_data = await user_collection.find_one({'id': user_id}, projection={'balance': 1, 'saved_amount': 1})

    if user_data:
        saved_amount = user_data.get('saved_amount', 0)

        if amount > saved_amount:
            await update.message.reply_text("Insufficient saved amount to withdraw.")
            return

        new_saved_amount = saved_amount - amount

        # Update user balance and saved amount
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': amount, 'saved_amount': -amount}})

        await update.message.reply_text(f"You withdrew Ŧ{amount} from your bank account.")
    else:
        await update.message.reply_text("User data not found.")
