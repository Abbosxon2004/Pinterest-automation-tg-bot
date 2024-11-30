import os
import time
import requests
from dotenv import load_dotenv
from send_tg_message import send_telegram_message
from gemini_generator import generate_gemini_text

load_dotenv()

BASE_URL = "https://api-sandbox.pinterest.com/v5/"
ACCESS_TOKEN = os.environ['PINTEREST_TOKEN']


def get_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        'Accept': 'application/json',
    }


# Fetch all boards with pagination
async def get_boards():
    await send_telegram_message("Boards are checking!")

    params = {
        "page_size": 200,
    }

    boards = []
    next_bookmark = None

    while True:
        if next_bookmark:
            params["bookmark"] = next_bookmark

        url = f"{BASE_URL}boards"
        response = requests.get(url, headers=get_headers(), params=params)

        if response.status_code == 200:
            data = response.json()
            boards.extend(data.get("items", []))
            next_bookmark = data.get("bookmark")

            # If there's no bookmark, we've reached the last page
            if not next_bookmark:
                break
        else:
            await send_telegram_message(f"Boards fetching is failed:\n {response.status_code} - {response.text}")
            break

    return boards


# Check if a board exists or create a new one
async def get_or_create_board(board_name):
    boards = await get_boards()
    await send_telegram_message(f"Board {board_name} is being checked!")
    for board in boards:
        if board['name'].lower() == board_name.lower():
            await send_telegram_message(f"Board is found: {board_name}\nDescription: {board['description']}")
            return board['id']

    # If board doesn't exist, create a new one
    return await create_board(board_name)


# Create a new board
async def create_board(board):
    await send_telegram_message("New board is creating!")

    prompt = f"""Generate beautiful description for this board name about traveling: {board}. Format the response as follows:
    Description: <description>
    """
    generated_text = generate_gemini_text(prompt)
    lines = generated_text.split("\n")

    description= f"Board for {board} travel tips and videos."
    for line in lines:
        if line.lower().startswith("description:"):
            description = line[len("Description:"):].strip()

    payload = {
        "name": board,
        "description": description,
    }
    url = f"{BASE_URL}boards/"
    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code == 201:
        board_data = response.json()
        print(f"Board '{board}' is created successfully!")
        await send_telegram_message(f"Board is created: {board}\n Description: {board_data['description']}")
        return board_data.get('id')
    else:
        print(f"Error creating board: {response.status_code} - {response.text}")
        await send_telegram_message(f"Error creating board: {response.status_code} - {response.text}")
    return None

# Create media by video url
async def upload_video_to_pinterest(telegram_video_url):
    # Step 1: Check if the media is already registered
    url = f"{BASE_URL}media/"
    headers = get_headers()
    payload = {"media_type": "video"}

    register_response = requests.post(url, headers=headers, json=payload)

    if register_response.status_code == 409:  # Conflict means the media is already registered
        print("Media is already registered!")
        media_data = register_response.json()
        media_id = media_data["media_id"]
        return media_id
    elif register_response.status_code != 201:
        print(f"Error registering video upload: {register_response.status_code} - {register_response.text}")
        return None

    media_data = register_response.json()
    media_id = media_data["media_id"]
    upload_url = media_data["upload_url"]
    upload_parameters = media_data["upload_parameters"]

    print(f"Media registered. Media ID: {media_id}")
    await send_telegram_message("Video upload is being registered! And checking")

    # Step 2: Fetch the video file from Telegram
    with requests.get(telegram_video_url, stream=True) as telegram_response:
        if telegram_response.status_code != 200:
            print(f"Error fetching video from Telegram: {telegram_response.status_code} - {telegram_response.text}")
            return None

        # Step 3: Upload the video to Pinterest's AWS bucket
        files = {"file": ("video.mp4", telegram_response.raw, "video/mp4")}

        upload_response = requests.post(upload_url, data=upload_parameters, files=files)

        if upload_response.status_code != 204:  # 204 No Content indicates success
            print(f"Error uploading video to AWS: {upload_response.status_code} - {upload_response.text}")
            return None

        print("Video uploaded successfully to Pinterest's AWS bucket!")

    # Step 4: Poll to confirm upload status
    confirm_url = f"{BASE_URL}media/{media_id}"
    for _ in range(10):  # Poll up to 10 times
        confirm_response = requests.get(confirm_url, headers=headers)

        if confirm_response.status_code != 200:
            print(f"Error confirming video upload: {confirm_response.status_code} - {confirm_response.text}")
            return None

        confirm_data = confirm_response.json()
        status = confirm_data.get("status")

        if status == "succeeded":
            print("Video upload confirmed!")
            await send_telegram_message("Video uploading succeeded!")
            return media_id
        elif status == "failed":
            print("Video upload failed!")
            return None

        print(f"Upload status: {status}. Retrying in 5 seconds...")
        time.sleep(5)  # Wait before retrying

    print("Video upload did not succeed within the timeout.")
    return None


# Create a pin on the board
async def create_pinterest_pin(board_id, video_url,thumbnail_url, title, description, tags):
    await send_telegram_message("Pin is creating!")

    # Upload video and get media_id
    media_id = await upload_video_to_pinterest(video_url)
    if not media_id:
        await send_telegram_message("Failed to upload video.")
        return

    payload = {
        "board_id": board_id,
        "title": title,
        "description": description,
        "tags": tags.split(","),
        "media_source": {
            "source_type": "video_id",  # Correct source_type for video
            "media_id": media_id,  # Media ID received from the upload
            "cover_image_url": thumbnail_url  # Thumbnail or cover image URL
        }
    }

    url = f"{BASE_URL}pins/"

    try:
        response = requests.post(url, headers=get_headers(), json=payload)

        if response.status_code == 201:
            print("Pin created successfully!")
            await send_telegram_message("Pin created successfully!!!")
        else:
            print(f"Error creating pin: {response.status_code} - {response.text}")
            await send_telegram_message(f"Pin creation failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        await send_telegram_message(f"Pin creation failed: {e}")


# Handle Pinterest tasks, including fetching or creating the board and adding the pin
async def handle_pinterest_task(video_url,thumbnail_url, processed_data):
    await send_telegram_message("Pinterest process is started")

    board = processed_data["board"]
    board_id = await get_or_create_board(board+" test")

    if board_id:
        await create_pinterest_pin(
            board_id=board_id,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            title=processed_data["title"],
            description=processed_data["description"],
            tags=processed_data["tags"]
        )
    else:
        await send_telegram_message("Pinterest process is failed")
