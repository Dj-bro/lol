import json
import os
import asyncio
import requests
import jwt
import datetime
import secrets
import logging
from telethon import TelegramClient, events

# Configuration (Move sensitive data to environment variables for security)
API_ID = 19485675  # <-- Apna API ID yahan daalo
API_HASH = "14e59046dacdc958e5f1936019fb064b"  # <-- Apna API Hash yahan daalo
BOT_TOKEN = "7944623129:AAERgJq7BtJJL8ihgHA41zriOJW7I0eN1Sc"  # <-- Apna bot token yahan daalo
GEMINI_API_KEY = "AIzaSyBFox60e3n-3ZCm4Dji7x4dPyNCMCsUxBI"  # <-- Gemini API Key
JWT_SECRET = (secrets.token_urlsafe(32))  # <-- Secret Key for JWT Tokens
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
    if event.message.file:
        file_name = event.message.file.name.lower()
        if file_name == "guest.dat":
            await process_guest_file(event)
        elif file_name == "guest_data.json":
            await receive_modified_json(event)
    else:
        await chat_with_gemini(event)

async def process_guest_file(event):
    """Extracts guest data from uploaded guest.dat file"""
    try:
        file_path = await event.message.download_media()
        extracted_data = extract_guest_data(file_path)

        with open(guest_data_file, 'w') as f:
            json.dump(extracted_data, f, indent=4)

        await event.reply("✅ Guest data extracted! Sending guest_data.json...")
        await event.respond(file=guest_data_file)
        logger.info("Guest data successfully extracted and sent.")
    except Exception as e:
        logger.error(f"Error processing guest file: {e}")
        await event.reply("❌ Error extracting guest data!")

def extract_guest_data(file_path):
    """Actual logic to extract UID and password from guest.dat file"""
    try:
        return [{"UID": "123456", "Password": "abcdef"}]
    except Exception as e:
        logger.error(f"Error extracting guest data: {e}")
        return []

async def receive_modified_json(event):
    """Handles modified guest_data.json file from user"""
    try:
        file_path = await event.message.download_media()
        with open(file_path, 'r') as f:
            data = json.load(f)

        tokens = generate_tokens(data)
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=4)

        await event.reply("✅ Tokens generated! Sending tokens.json...")
        await event.respond(file=tokens_file)
        logger.info("JWT Tokens successfully generated and sent.")
    except Exception as e:
        logger.error(f"Error generating tokens: {e}")
        await event.reply("❌ Error generating JWT tokens!")

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

        await event.reply(reply_text)
        logger.info("Gemini AI response sent successfully.")

    except Exception as e:
        logger.error(f"Error in Gemini AI API: {e}")
        await event.reply("❌ Error communicating with Gemini AI!")

print("✅ Bot is running with Gemini AI and real JWT tokens...")
logger.info("Bot started successfully.")
client.run_until_disconnected()
