import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import google.generativeai as genai
from send_message import send_telegram_message
from pinterest import handle_pinterest_task

load_dotenv()

# Configure the API key for Gemini
genai.configure(api_key=os.environ['GEN_AI_TOKEN'])

# Function to generate text using Gemini AI
def generate_gemini_text(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

# Function to process the caption
def process_caption(caption):
    prompt = f"""
    Extract the title for a travel-related caption. Add country name to title in the last.
    Here is the caption: {caption}.
    Also generate a description with 2-3 sentences, and 4-5 tags(without hashtags) related to that caption.
    Additionally, extract the country name from the caption and format the response as follows:
    Title: <title>
    Description: <description>
    Tags: <tags>
    Country: <country>
    """

    generated_text = generate_gemini_text(prompt)
    lines = generated_text.split("\n")
    
    title, description, tags, country = "No title", "No description", "No tags", "Unknown"
    for line in lines:
        if line.lower().startswith("title:"):
            title = line[len("Title:"):].strip()
        elif line.lower().startswith("description:"):
            description = line[len("Description:"):].strip()
        elif line.lower().startswith("tags:"):
            tags = line[len("Tags:"):].strip()
        elif line.lower().startswith("country:"):
            country = line[len("Country:"):].strip()

    return {"title": title, "description": description, "tags": tags, "country": country}

# Function to handle the /start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi! Send me a video, and I'll create a video pin for you on Pinterest.")

# Function to handle video messages
async def handle_video(update: Update, context: CallbackContext) -> None:
    video = update.message.video
    caption = update.message.caption

    if video:
        file_id = video.file_id
        file = await context.bot.get_file(file_id)
        download_url = file.file_path

        if caption:
            # Process the caption
            processed_data = process_caption(caption)

            # Respond to the user
            await update.message.reply_text(
                f"Title:  {processed_data['title']}\n\n"
                f"Description:  {processed_data['description']}\n\n"
                f"Tags:  {processed_data['tags']}\n\n"
                f"Country:  {processed_data['country']}\n\n"
                f"Video Link: {download_url}"
            )

            # Pass the processed data and video URL to Pinterest handler
            await send_telegram_message("Pinterest process is started")
            await handle_pinterest_task(download_url, processed_data)

        else:
            await update.message.reply_text("No caption provided. Unable to process the video.")
    else:
        await update.message.reply_text("Please send a valid video file.")

# Main function
def main():
    BOT_TOKEN = os.environ['BOT_TOKEN']
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    application.run_polling()

if __name__ == "__main__":
    main()