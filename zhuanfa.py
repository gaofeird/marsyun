# -*- coding: utf-8 -*-
# ���������
from telethon.sync import TelegramClient
from telethon import events

# ����Telegram API�����Ϣ
api_id = 19559732
api_hash = '52a59514d7db9bc29c0c94a6dbc3dbe3'
source_chat = -1001654299303
destination_chat = -1001813970852

# ����TelegramClient����
client = TelegramClient('zhuanfa', api_id, api_hash)

# ����Ҫ��صĹؼ���
keywords = ['export', 'keyword2', 'keyword3']

# ������Ϣת������
@client.on(events.NewMessage(chats=source_chat))
async def forward_to_destination(event):
    # �ж���Ϣ�Ƿ�����ؼ���
    for keyword in keywords:
        if keyword in event.message.message:
            # ת����Ϣ��Ŀ��Ⱥ��
            await client.send_message(destination_chat, event.message.message)

# ����TelegramClient
client.start()
client.run_until_disconnected()
