import random
import asyncio
import logging
from telethon import TelegramClient

# Use your own values from my.telegram.org
api_id = 19559732
api_hash = '52a59514d7db9bc29c0c94a6dbc3dbe3'

# Configure the logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the async function to send the messages
async def send_messages():
    async with TelegramClient('id_' + str(api_id), api_id, api_hash) as client:
        # Send message to @Sillgirl_bot
        logging.info('Sending message to @Sillgirl_bot...')
        await client.send_message('@Sillgirl_bot', '重启')
        await asyncio.sleep(random.randint(1, 300))
        logging.info('Message sent to @Sillgirl_bot.')

        # Send message to @yyjc_checkin_bot
        logging.info('Sending message to @yyjc_checkin_bot...')
        await client.send_message('@yyjc_checkin_bot', '/checkin')
        await asyncio.sleep(random.randint(1, 300))
        logging.info('Message sent to @yyjc_checkin_bot.')

        # Send message to @yyjc_checkin_bot
        logging.info('Sending message to @yyjc_checkin_bot...')
        await client.send_message('@yyjc_checkin_bot', '/query')
        await asyncio.sleep(random.randint(1, 300))
        logging.info('Message sent to @yyjc_checkin_bot.')

        # Send message to @sgsillyGirl_bot
        logging.info('Sending message to @sgsillyGirl_bot...')
        await client.send_message('@sgsillyGirl_bot', '重启')
        await asyncio.sleep(random.randint(1, 300))
        logging.info('Message sent to @sgsillyGirl_bot.')

# Call the async function and run the event loop
asyncio.run(send_messages())
