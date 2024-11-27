import os
import requests
from dotenv import load_dotenv
from send_message import send_telegram_message

load_dotenv()

BASE_URL = "https://api.pinterest.com/v5/"
ACCESS_TOKEN = os.environ['PINTEREST_TOKEN']


def get_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        'Accept': 'application/json',
    }

async def make_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = get_headers()
    
    try:
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during {method} request to {endpoint}: {e}")
        await send_telegram_message(f"Error during {method} request to {endpoint}: {e}")
        return None

async def get_or_create_board(board_name):
    await send_telegram_message("Boards are checking!")
    # Fetch all boards
    boards_data = await make_request("GET", "boards", ACCESS_TOKEN)
    if not boards_data:
        return None

    boards = boards_data.get('items', [])

    # Check if a board with the given name exists
    for board in boards:
        if board['name'].lower() == board_name.lower():
            await send_telegram_message("Board is found: {board_name}")
            return board['id']

    # If not found, create a new board
    return await create_board(board_name)

async def create_board(board_name):
    await send_telegram_message("Board is creating!")
    payload = {
        "name": board_name,
        "description": f"Board for {board_name} travel tips and videos."
    }
    board_data = await make_request("POST", "boards/", ACCESS_TOKEN, data=payload)
    if board_data:
        print(f"Board '{board_name}' created successfully!")
        await send_telegram_message("Board is created: {board_name}")
        return board_data.get('id')
    return None

async def create_pinterest_pin(board_id, video_url, title, description, tags, country):
    await send_telegram_message("Pin is creating!")
    payload = {
        "board_id": board_id,
        "media": {"video": {"url": video_url}},
        "title": title,
        "description": description,
        "tags": tags.split(","),
        "alt_text": f"A travel video from {country}"
    }
    pin_data = await make_request("POST", "pins/", ACCESS_TOKEN, data=payload)
    if pin_data:
        print("Pin created successfully!")
        await send_telegram_message("Pin created successfully!")
    else:
        print("Failed to create the pin.")
        await send_telegram_message("Pin created successfully!")


async def handle_pinterest_task(video_url, processed_data):
    country = processed_data["country"]
    board_id = await get_or_create_board( country) 
    await send_telegram_message("Pinterest is handling!")
    await create_pinterest_pin(
        board_id=board_id,
        video_url=video_url,
        title=processed_data["title"],
        description=processed_data["description"],
        tags=processed_data["tags"],
        country=country,
    )