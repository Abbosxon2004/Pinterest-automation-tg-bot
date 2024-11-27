import os
from telegram import Bot

async def send_telegram_message(message):
    
    bot = Bot(token=os.environ["BOT_TOKEN"])
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    try:
        await bot.send_message(chat_id=int(chat_id), text=message)
        print(f"Message sent to Telegram: {message}")
    except Exception as e:
        print(f"Failed to send message to Telegram: {e}")