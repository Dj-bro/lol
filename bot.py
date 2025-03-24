import json
import asyncio
import requests
import jwt
import datetime
import logging
import secrets
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# Configuration
API_ID = 19485675  # <-- Apna API ID yahan daalo
API_HASH = "14e59046dacdc958e5f1936019fb064b"  # <-- Apna API Hash yahan daalo
BOT_TOKEN = "7944623129:AAEiTQCnSoiONVnP8dnsbSXRFVo6MfxgWd8"  # <-- Apna bot token yahan daalo
GEMINI_API_KEY = "AIzaSyAXTmJbFfFQBU0bFKpswCyfCytoCL7LfLU"  # <-- Gemini API Key
JWT_SECRET = secrets.token_urlsafe(32)  # <-- Secret Key for JWT Tokens
JWT_ALGORITHM = "HS256"

guest_data_file = "guest_data.json"
tokens_file = "tokens.json"

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize Telegram Client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage)
async def handle_messages(event):
    """Handle text messages and file uploads"""
    try:
        if event.message.file:
            file_name = event.message.file.name.lower()
            if file_name.endswith(".dat") or file_name.endswith(".json"):
                await process_file(event, file_name)
        else:
            await chat_with_gemini(event)
    except FloodWaitError as e:
        logger.warning(f"Flood wait detected! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        await handle_messages(event)  # Retry after sleep
    except Exception as e:
        logger.error(f"Unexpected error in handle_messages: {e}")

async def process_file(event, file_name):
    """Process uploaded files based on their format"""
    try:
        file_path = await event.message.download_media()
        if file_name.endswith(".dat"):
            extracted_data = extract_guest_data(file_path)
            if extracted_data:
                with open(guest_data_file, 'w') as f:
                    json.dump(extracted_data, f, indent=4)
                await safe_send(event, "✅ Guest data extracted! Sending guest_data.json...")
                await safe_send(event, file=guest_data_file)
                logger.info("Guest data successfully extracted and sent.")
            else:
                await safe_send(event, "❌ No valid guest data found!")
        elif file_name.endswith(".json"):
            await receive_modified_json(file_path, event)
    except Exception as e:
        logger.error(f"Error processing file {file_name}: {e}")
        await safe_send(event, f"❌ Error processing {file_name}!")

def extract_guest_data(file_path):
    """Extract UID and password from guest.dat file"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read().decode(errors='ignore')
            return [{"UID": "123456", "Password": "abcdef"}]  # Dummy data, modify as needed
    except Exception as e:
        logger.error(f"Error extracting guest data: {e}")
        return []

async def receive_modified_json(file_path, event):
    """Handles modified guest_data.json file from user"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        tokens = generate_tokens(data)
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=4)
        await safe_send(event, "✅ Tokens generated! Sending tokens.json...")
        await safe_send(event, file=tokens_file)
        logger.info("JWT Tokens successfully generated and sent.")
    except Exception as e:
        logger.error(f"Error generating tokens: {e}")
        await safe_send(event, "❌ Error generating JWT tokens!")

def generate_tokens(data):
    """Generate JWT tokens for each UID"""
    tokens = []
    for user in data:
        try:
            payload = {
                "UID": user["UID"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            tokens.append({"UID": user["UID"], "Token": token})
        except Exception as e:
            logger.error(f"Error generating token for {user['UID']}: {e}")
    return tokens

async def chat_with_gemini(event):
    """Handles AI chat using Gemini API"""
    try:
        user_message = event.message.text
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": user_message}]}]}
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        
        if "candidates" in response_json:
            reply_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            reply_text = "❌ Gemini AI response error!"
        
        await safe_send(event, reply_text)
        logger.info("Gemini AI response sent successfully.")
    except Exception as e:
        logger.error(f"Error in Gemini AI API: {e}")
        await safe_send(event, "❌ Error communicating with Gemini AI!")

async def safe_send(event, message=None, file=None):
    """Send messages safely with flood wait handling"""
    try:
        if file:
            await event.respond(file=file)
        else:
            await event.reply(message)
    except FloodWaitError as e:
        logger.warning(f"Flood wait detected! Sleeping for {e.seconds} seconds before retrying...")
        await asyncio.sleep(e.seconds)
        await safe_send(event, message, file)  # Retry after waiting

print("✅ Bot is running with Gemini AI and real JWT tokens...")
logger.info("Bot setup successfully.")
client.run_until_disconnected()
