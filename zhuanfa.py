# -*- coding: utf-8 -*-
# 导入所需库
from telethon.sync import TelegramClient
from telethon import events

# 填入Telegram API相关信息
api_id = 19559745
api_hash = '52a59514d54b9bc29c0c9488dbc3dbe3'
source_chat = -1001654599303
destination_chat = -1001866970852

# 创建TelegramClient对象
client = TelegramClient('zhuanfa', api_id, api_hash)

# 设置要监控的关键字
keywords = ['export', 'keyword2', 'keyword3']

# 定义消息转发函数
@client.on(events.NewMessage(chats=source_chat))
async def forward_to_destination(event):
    # 判断消息是否包含关键字
    for keyword in keywords:
        if keyword in event.message.message:
            # 转发消息到目标群组
            await client.send_message(destination_chat, event.message.message)

# 运行TelegramClient
client.start()
client.run_until_disconnected()
