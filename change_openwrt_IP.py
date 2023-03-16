import requests
import json
import time
import threading
import paramiko
from flask import Flask, request
from urllib.parse import quote
import re
from time import sleep


# 设置Telegram机器人Token
bot_token = '6131223232:AAEpGKuOD2fbj23S9y7MA81DY9P0XHQy-0c'

# 设置OpenWrt路由器的IP地址、用户名和密码
router_ip = '192.168.191.182'
router_username = 'root'
router_password = 'kqpsc5ePa8HUy3B'

# 设置Webhook的地址和端口号
webhook_url = 'https://webhook.vpscn.com'
webhook_port = 88

# 设置证书和密钥路径
cert = '/root/your-self-signed-certificate.crt'
key = '/root/your-private-key.key'

# 获取OpenWrt路由器的外网IP地址
def get_router_public_ip():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, port=22, username=router_username, password=router_password)
    stdin, stdout, stderr = ssh.exec_command('curl -s http://members.3322.org/dyndns/getip')
    router_public_ip = stdout.read().decode('utf-8').strip()
    ssh.close()
    return router_public_ip

# 重新拨号并获取新的IP地址
def redial_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, port=22, username=router_username, password=router_password)
    ssh.exec_command('ifdown wan && ifup wan')
    ssh.close()

    max_wait_time = 300  # 最大等待时间为 5 分钟
    start_time = time.time()
    old_ip = get_router_public_ip()
    while time.time() - start_time < max_wait_time:
        new_ip = get_router_public_ip()
        if new_ip != old_ip:
            return new_ip
        time.sleep(5)  # 每隔 5 秒检查一次 IP 地址是否变化
    return old_ip  # 如果超时还未获取到新的 IP 地址，返回旧的 IP 地址

# 处理来自Telegram机器人的消息和指令
def handle_message(message):
    print(message)
    chat_id = message['chat']['id']
#    chat_id = '2001427842'
    if 'text' in message:
        command = message['text']
        if command == '/ip':
            send_telegram_message(chat_id, 'OpenWrt路由器已收到请求，请稍候⏳。', delete_after=15)
            router_public_ip = get_router_public_ip()
            send_telegram_message(chat_id, f'OpenWrt路由器的外网IP地址为: {router_public_ip}🚀', delete_after=100)
        elif command == '/reboot':
            reboot_router()
            send_telegram_message(chat_id, 'OpenWrt路由器已重启，请稍候，正在重新连接⏳，120秒后重新获取IP🚀。', delete_after=120)
            
        elif command == '/redial':
            send_telegram_message(chat_id, 'OpenWrt路由器已重拨，请稍候，60秒后重新获取IP⏳', delete_after=120)
#            new_router_public_ip = redial_router()            
#            new_parts = new_router_public_ip.split('.')
#            if len(new_parts) == 4:
#                new_prefix, new_middle, new_suffix = new_parts[0], '*'*len(new_parts[1]), new_parts[3]
#                new_masked_ip = f"{new_prefix}.***.***.{new_suffix}"
#                send_telegram_message(chat_id, f'OpenWrt路由器的新外网IP地址为: {new_masked_ip}', delete_after=15)
#            send_telegram_message(chat_id, f'OpenWrt路由器的新外网IP地址为: {new_router_public_ip}', delete_after=15)
#            else:
#                send_telegram_message(chat_id, '获取IP地址失败，请重试', delete_after=15)
            update = request.get_json()
            print(update)
# 发送消息到Telegram机器人，并在一定时间后删除该条消息
def send_telegram_message(chat_id, message, delete_after=3):
    # 发送消息
    response = requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={quote(message)}')
    print(response.json())  # 调试语句
    message_id = response.json()['result']['message_id']
    # 如果设置了 delete_after，就在指定时间后删除该条消息
    if delete_after is not None:
        message_id = json.loads(response.content.decode('utf-8'))['result']['message_id']
        threading.Timer(delete_after, delete_telegram_message, args=[chat_id, message_id]).start()
# 删除Telegram机器人的消息
def delete_telegram_message(chat_id, message_id):
    requests.get(f'https://api.telegram.org/bot{bot_token}/deleteMessage?chat_id={chat_id}&message_id={message_id}')

# 重启OpenWrt路由器
def reboot_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, port=22, username=router_username, password=router_password)
    ssh.exec_command('reboot')
    ssh.close()

# 启动Flask Web服务器
app = Flask(__name__)
'''
# 接收Telegram机器人的Webhook请求
@app.route(f'/{bot_token}', methods=['POST'])
def handle_webhook_request():
    if request.method == 'POST':
        update = request.get_json()
        if 'message' in update:
            message = update['message']
            handle_message(message)
        # 获取更新中的 chat_id 和 message_id
        chat_id = update['message']['chat']['id']
        message_id = update['message']['message_id']

        # 如果消息是命令（以 '/' 开头），则删除它
        if update['message']['text'].startswith('/'):
            delete_message(chat_id, message_id)    
        return 'ok'
        '''
# 接收Telegram机器人的Webhook请求
@app.route(f'/{bot_token}', methods=['POST'])
def handle_webhook_request():
    if request.method == 'POST':
        update = request.get_json()
        if 'message' in update:
            message = update['message']
            handle_message(message)

            # 获取更新中的 chat_id 和 message_id
            if 'chat' in message and 'id' in message['chat']:
                chat_id = message['chat']['id']
            else:
                chat_id = None

            if 'message_id' in message:
                message_id = message['message_id']
            else:
                message_id = None

            # 如果消息是命令（以 '/' 开头），则删除它
            if 'text' in message and message['text'].startswith('/'):
                delete_message(chat_id, message_id)    
        return 'ok'
        
        update = request.get_json()
        print(update)
# 这是 Telegram Bot API 的基本 URL
BASE_URL = f'https://api.telegram.org/bot{bot_token}/'

# 用于删除消息的方法
def delete_message(chat_id, message_id):
    url = BASE_URL + f'deleteMessage?chat_id={chat_id}&message_id={message_id}'
    response = requests.get(url)
    return json.loads(response.content)
    
# 设置Telegram机器人的Webhook地址
def set_telegram_webhook():
    cert = '/root/your-self-signed-certificate.crt'
    key = '/root/your-private-key.key'
    requests.get(f'https://api.telegram.org/bot{bot_token}/deleteWebhook')
    time.sleep(1)
#    response = requests.post(f'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}:{webhook_port}/{bot_token}', files={'certificate': open(cert, 'rb')}, data={'url': f'{webhook_url}:{webhook_port}/{bot_token}'})
    response = requests.post(f'https://api.telegram.org/bot{bot_token}/setWebhook', 
                         data={'url': f'{webhook_url}:{webhook_port}/{bot_token}'},
                         files={'certificate': (cert, open(cert, 'rb'), 'application/x-pem-file')})

    print(response.text)

if __name__ == '__main__':
    set_telegram_webhook()
    app.run(host='0.0.0.0', port=webhook_port, ssl_context=(cert, key))
'''
# Flask Web应用
app = Flask(__name__)

# Telegram机器人接收消息的Webhook
@app.route(f'/{bot_token}', methods=['POST'])
def telegram_webhook():
    message = request.get_json()
    if message is not None:
        handle_message(message)
    return 'ok'

# 启动Flask Web应用
if __name__ == '__main__':
    context = (cert, key)
    app.run(host='0.0.0.0', port=webhook_port, ssl_context=context)
# 处理Telegram机器人的Webhook请求
@app.route('/', methods=['POST'])
def handle_webhook_request():
    update = request.get_json()
    if 'message' in update:
        handle_message(update['message'])
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=webhook_port, ssl_context=(cert, key))
'''
