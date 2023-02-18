cert = '/root/your-self-signed-certificate.crt'
key = '/root/your-private-key.key'
import requests
import json
import time
import threading
import paramiko
from flask import Flask, request
from urllib.parse import quote
import re

# 设置Telegram机器人Token
bot_token = ''
# 设置OpenWrt路由器的IP地址、用户名和密码
#router_ip = '192.168.191.182'    
router_ip = '192.168.191.139'
router_username = 'root'
#router_password = 'kqpsc5ePa8HUy3B'    #182password
router_password = 'YB8YJeNyCUJdHUb'     #139password
# 设置Webhook的地址和端口号
webhook_url = 'https://'
webhook_port = 88

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
    time.sleep(50)  # 等待30秒让路由器重新获取IP地址    
    return get_router_public_ip()

# 处理来自Telegram机器人的消息和指令
'''
def handle_message(message):
    print(message)
    chat_id = message['chat']['id']
    if 'text' in message:
        command = message['text']
        if command == '/ip':
            router_public_ip = get_router_public_ip()
            prefix, middle, suffix = router_public_ip.split('.')
            masked_middle = '*' * len(middle)
            masked_ip = f"{prefix}.{masked_middle}.{suffix}"
            send_telegram_message(chat_id, f'OpenWrt路由器的外网IP地址为: {masked_ip}', delete_after=15)
'''
def handle_message(message):
    print(message)
#    chat_id = '2001427842'
    chat_id = message['chat']['id']
    if 'text' in message:
        command = message['text']
        if command == '/ip':
            router_public_ip = get_router_public_ip()
#            parts = router_public_ip.split('.')
#            if len(parts) == 4:
#                prefix, middle, suffix = parts[0], '*'*len(parts[1]), parts[3]
#                masked_ip = f"{prefix}.***.***.{suffix}"
#                send_telegram_message(chat_id, f'OpenWrt路由器的外网IP地址为: {masked_ip}', delete_after=15)
            send_telegram_message(chat_id, f'OpenWrt路由器的外网IP地址为: {router_public_ip}', delete_after=15)
#            else:
#                send_telegram_message(chat_id, '获取IP地址失败，请重试', delete_after=15)
        elif command == '/reboot':
            reboot_router()
            send_telegram_message(chat_id, 'OpenWrt路由器已重启，请稍候重新连接。', delete_after=60)
        elif command == '/redial':
            new_router_public_ip = redial_router()
#            new_parts = new_router_public_ip.split('.')
#            if len(new_parts) == 4:
#                new_prefix, new_middle, new_suffix = new_parts[0], '*'*len(new_parts[1]), new_parts[3]
#                new_masked_ip = f"{new_prefix}.***.***.{new_suffix}"
#                send_telegram_message(chat_id, f'OpenWrt路由器的新外网IP地址为: {new_masked_ip}', delete_after=15)
            send_telegram_message(chat_id, f'OpenWrt路由器的新外网IP地址为: {new_router_public_ip}', delete_after=15)
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
    # 如果设定了删除时间，开启一个线程在指定时间后删除该条消息
    if delete_after is not None:
        threading.Timer(delete_after, delete_telegram_message, args=(chat_id, message_id)).start()
    
# 删除消息
def delete_telegram_message(chat_id, message_id):
    requests.get(f'https://api.telegram.org/bot{bot_token}/deleteMessage?chat_id={chat_id}&message_id={message_id}')

''' 
def webhook(request):
    # 从 request 中提取 message_id 和 chat_id
    message_id = request.json["message"]["message_id"]
    chat_id = request.json["message"]["chat"]["id"]

    # 判断消息是否是命令
    if "/command" in request.json["message"]["text"]:
        # 调用 deleteMessage API 删除该消息
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id}
        )
        if not response.ok:
            print(response.text)

def delete_message(bot, chat_id, message_id):
    time.sleep(3)
    bot.delete_message(chat_id, message_id)

def handle_command(update, context):
    command = update.message.text.lower()

    # 检查消息是否为指定的命令
    if command.startswith('/ip') or command.startswith('/reboot') or command.startswith('/redial'):
        # 启动新线程，在3秒钟后删除消息
        thread = threading.Thread(target=delete_message, args=(context.bot, update.message.chat_id, update.message.message_id))
        thread.start()

 
# 发送消息到Telegram机器人
def send_telegram_message(chat_id, message):
#    requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}')
    requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={quote(message)}')

# 发送一个自动删除消息
def send_auto_delete_message(chat_id, message, timeout=10):
    # 发送消息并获取消息ID
    requests = requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text=(message)')
    message_id = response.json()['result']['message_id']
    # 等待指定的时间
    time.sleep(timeout)
    # 删除消息
    requests.get(f'https://api.telegram.org/bot{bot_token}/deleteMessage?chat_id={chat_id}&message_id=(message_id)')
'''    
# 重启OpenWrt路由器
def reboot_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, port=22, username=router_username, password=router_password)
    ssh.exec_command('reboot')
    ssh.close()

# 启动Flask Web服务器
app = Flask(__name__)

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
