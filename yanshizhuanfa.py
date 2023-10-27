# -*- coding: utf-8 -*-
# 导入所需库
import random
import asyncio
from telethon.sync import TelegramClient
from telethon import events

# 填入Telegram API相关信息
api_id = 19534732
api_hash = '52a59514d7db23429c0c94a6dbc3dbe3'
source_chat = -1001744366345
destination_chat = -1001821970852

# 创建TelegramClient对象
client = TelegramClient('zhuanfa2', api_id, api_hash)

# 设置要监控的关键字
keywords = ['https', 'keyword2', 'keyword3']

# 定义消息转发函数
@client.on(events.NewMessage(chats=source_chat))
async def forward_to_destination(event):
    # 判断消息是否包含关键字
    for keyword in keywords:
        if keyword in event.message.message:
            # 随机生成延迟时间
            delay_time = random.randint(1, 30)
            # 延迟一段时间后，将消息转发到目标群组
            await asyncio.sleep(delay_time)
            await client.send_message(destination_chat, event.message.message)

# 运行TelegramClient
client.start()
client.run_until_disconnected()