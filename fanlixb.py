# -*- coding: utf-8 -*-
# ���������
from telethon.sync import TelegramClient
from telethon import events

# ����Telegram API�����Ϣ
api_id = 19559732
api_hash = '52a59514d7db9bc29c0c94a6dbc3dbe3'
source_chat = -1001609456179
destination_chat = -1001852714113

# ����TelegramClient����
client = TelegramClient('fanlixb', api_id, api_hash)

# ����Ҫ��صĹؼ���
keywords = ['https', 'keyword2', 'keyword3']

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
