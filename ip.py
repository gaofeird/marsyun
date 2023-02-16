cert = '/root/your-self-signed-certificate.crt'
key = '/root/your-private-key.key'
import requests
import json
import time
import paramiko
from flask import Flask, request
from urllib.parse import quote

# 设置Telegram机器人Token
bot_token = 'your-bot-token'
# 设置OpenWrt路由器的IP地址、用户名和密码
router_ip = 'your-router-ip'
router_username = 'your-username'
router_password = 'your-password'
# 设置Webhook的地址和端口号
webhook_url = 'your-webhook-url'
webhook_port = 8443

# 获取OpenWrt路由器的外网IP地址
def get_router_public_ip():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(router_ip, port=22, username=router_username, password=router_password)
    stdin, stdout, stderr = ssh.exec_command('curl -s ifconfig.me')
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
    time.sleep(30)  # 等待30秒让路由器重新获取IP地址
    return get_router_public_ip()

# 处理来自Telegram机器人的消息和指令
def handle_message(message):
    print(message)
#    chat_id = 'your-chat_id'
    chat_id = message['chat']['id']
    if 'text' in message:
        command = message['text']
        if command == '/ip':
            router_public_ip = get_router_public_ip()
            send_telegram_message(chat_id, f'OpenWrt路由器的外网IP地址为: {router_public_ip}')
        elif command == '/reboot':
            reboot_router()
            send_telegram_message(chat_id, 'OpenWrt路由器已重启，请稍候重新连接。')
        elif command == '/redial':
            new_router_public_ip = redial_router()
            send_telegram_message(chat_id, f'OpenWrt路由器的新外网IP地址为: {new_router_public_ip}')
            update = request.get_json()
            print(update)

# 发送消息到Telegram机器人
def send_telegram_message(chat_id, message):
#    requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}')
    requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={quote(message)}')

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
        return 'ok'
        update = request.get_json()
        print(update)

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
