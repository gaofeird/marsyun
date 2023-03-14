from telethon import TelegramClient, events

# Replace the placeholders with your own API ID, API hash and Telegram account phone number
API_ID = 19559732
API_HASH = "52a59514d7db9bc29c0c94a6dbc3dbe3"
PHONE_NUMBER = "+8613260850060"

# Replace the placeholders with the source chat/channel name, target chat/channel name, and keywords
SOURCE_NAME = "https://t.me/Marsgic_bot"
#SOURCE_NAME = "https://t.me/Wall_E_Group"
TARGET_NAME = "https://t.me/Sillgirl_bot"
KEYWORDS = ["没有自动车", "gaofei"]

# Initialize the client
client = TelegramClient("gjzzf", API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_NAME))
async def handler(event):
    message = event.message
    text = message.message.lower()
    # Check if the message contains any keywords
    if any(keyword in text for keyword in KEYWORDS):
        # Forward the message to the target chat/channel
        await client.forward_messages(TARGET_NAME, message)

if __name__ == '__main__':
    client.start()
    client.run_until_disconnected()
