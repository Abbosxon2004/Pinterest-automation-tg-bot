import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
from pinterest import handle_pinterest_task
from gemini_generator import generate_gemini_text

load_dotenv()

BOT_TOKEN = os.environ['BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# Function to process the caption
def process_caption(caption):
    prompt = f"""
    Extract the title for a travel-related caption. Add country name to title in the last.
    Here is the caption: {caption}.
    Also generate a description with 2-3 sentences,make it creative with beautiful emojis and 7-8 tags(with hashtags) related to that caption.
    Additionally, extract the country name from the caption and format the response as follows:
    Title: <title>
    Description: <description>
    Tags: <tags>
    Board: <country>
    """

    generated_text = generate_gemini_text(prompt)
    lines = generated_text.split("\n")
    
    title, description, tags, board = "", "", "", ""
    for line in lines:
        if line.lower().startswith("title:"):
            title = line[len("Title:"):].strip()
        elif line.lower().startswith("description:"):
            description = line[len("Description:"):].strip()
        elif line.lower().startswith("tags:"):
            tags = line[len("Tags:"):].strip()
        elif line.lower().startswith("board:"):
            board = line[len("Board:"):].strip()
            if board == "": "Unbelievable"

    return {"title": title, "description": description, "tags": tags, "board": board}

# Function to handle the /start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi! Send me a video, and I'll create a video pin for you on Pinterest.")

# Function to handle video messages
async def handle_video(update: Update, context: CallbackContext) -> None:

    # Check if the user's ID matches the authorized Telegram Chat ID
    if update.message.from_user.id != int(TELEGRAM_CHAT_ID):
        await update.message.reply_text("You are not authorized to use this bot. Please contact the admins.")
        return  # Stop further processing

    video = update.message.video
    caption = update.message.caption

    if video:
        file_id = video.file_id
        file = await context.bot.get_file(file_id)
        download_url = file.file_path


        thumbnail_file = await context.bot.get_file(video.thumbnail.file_id)
        thumbnail_url = thumbnail_file.file_path

        if caption:
            # Process the caption
            processed_data = process_caption(caption)

            # Respond to the user
            await update.message.reply_text(
                f"Title:  {processed_data['title']}\n\n"
                f"Description:  {processed_data['description']} {processed_data['tags']}\n\n"
                f"Board:  {processed_data['board']}\n\n"
                f"Video Link: {download_url}"
            )

            # Pass the processed data and video URL to Pinterest handler
            await handle_pinterest_task(download_url,thumbnail_url, processed_data)

        else:
            await update.message.reply_text("No caption provided. Unable to process the video.")
    else:
        await update.message.reply_text("Please send a valid video file.")

# Main function
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    application.run_polling()

if __name__ == "__main__":
    main()