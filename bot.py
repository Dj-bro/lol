import json
import os
import asyncio
import secrets
from telethon import TelegramClient, events
import openai

# Config file se data load karna
with open("config.json", "r") as f:
    config = json.load(f)

API_ID = config["API_ID"]
API_HASH = config["API_HASH"]
BOT_TOKEN = config["BOT_TOKEN"]
OPENAI_KEY = config["OPENAI_KEY"]

SECURITY_KEY = secrets.token_hex(32)  # Secure key generate

# Initialize OpenAI & Telegram Client
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
openai.api_key = OPENAI_KEY

guest_data_file = "guest_data.json"
tokens_file = "tokens.json"

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("Welcome! Send me guest.dat files to process or chat with AI.")

@client.on(events.NewMessage)
async def handle_messages(event):
    if event.message.file:
        await process_guest_file(event)
    else:
        await chat_with_ai(event)

async def process_guest_file(event):
    file_path = await event.message.download_media()
    extracted_data = extract_guest_data(file_path)
    
    with open(guest_data_file, 'w') as f:
        json.dump(extracted_data, f, indent=4)
    
    await event.reply("Guest data extracted successfully! Sending guest_data.json...")
    await event.respond(file=guest_data_file)

def extract_guest_data(file_path):
    # Dummy extraction logic (Replace with real extraction code)
    return [{"UID": "123456", "Password": "abcdef"}]

@client.on(events.NewMessage)
async def receive_modified_json(event):
    if event.message.file and event.message.file.name == "guest_data.json":
        file_path = await event.message.download_media()
        with open(file_path, 'r') as f:
            data = json.load(f)
        tokens = generate_tokens(data)
        
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=4)
        
        await event.reply("Tokens generated! Sending tokens.json...")
        await event.respond(file=tokens_file)

def generate_tokens(data):
    # Dummy token generation logic
    return [{"UID": d["UID"], "Token": "generated_jwt_token"} for d in data]

async def chat_with_ai(event):
    user_message = event.message.text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "user", "content": user_message}]
    )
    reply_text = response["choices"][0]["message"]["content"]
    await event.reply(reply_text)

print("Bot is running...")
client.run_until_disconnected()