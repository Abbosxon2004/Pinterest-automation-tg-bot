# Telegram to Pinterest Video Bot

## Overview
This bot allows users to upload videos via Telegram, processes the captions using generative AI, and uploads the videos as Pinterest pins with auto-generated titles, descriptions, and tags. The bot automates the process of creating visually appealing and SEO-optimized Pinterest pins for travel-related content.

---

## Features
- **Telegram Integration**: Accepts video uploads and captions from Telegram users.
- **AI-Powered Content Generation**: Uses Google Gemini AI to generate titles, descriptions, tags, and extract country names from captions.
- **Pinterest Integration**: Automatically creates Pinterest boards (if necessary) and uploads videos as pins.
- **Status Notifications**: Sends status updates back to the user via Telegram.

---

## Requirements
- Python 3.10 or higher
- Telegram Bot API token
- Pinterest API token
- Google Gemini AI token
- Environment variables for configuration

---

## Installation

### Clone the Repository:
```bash
git clone https://github.com/your-repo-name/telegram-to-pinterest-bot.git
cd telegram-to-pinterest-bot
```

## Set Up Environment Variables:
Create a .env file in the root directory with the following keys:
```
BOT_TOKEN=<your-telegram-bot-token>
TELEGRAM_CHAT_ID=<your-telegram-chat-id>
PINTEREST_TOKEN=<your-pinterest-api-token>
GEN_AI_TOKEN=<your-google-gemini-ai-token>
```

## Usage
### Start the Bot
```bash
    python main.py
```
### Interact with the Bot on Telegram
- Use the /start command to initialize the bot.
- Send a video with a caption. The bot will:
  - Process the caption using generative AI.
  - Generate:
    - Title
    - Description
    - Tags
    - Country name(Board name)
  - Upload the video as a pin to Pinterest.
  - Notify you via Telegram when the process is complete.