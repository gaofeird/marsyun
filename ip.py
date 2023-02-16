import requests
import json
import time
import paramiko
from flask import Flask, request

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

# 处理来自Telegram机器人的消息和指令
def handle_message(message):
    chat_id = message['chat']['id']
    if 'text' in message:
        command = message['text']
        if command == '/ip':
            router_public_ip = get_router_public_ip()
            send_telegram_message(chat_id, f'OpenWrt路由器的外网IP地址为: {router_public_ip}')

# 发送消息到Telegram机器人
def send_telegram_message(chat_id, message):
    requests.get(f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}')

# 启动Flask Web服务器
app = Flask(__name__)

# 接收Telegram机器人的Webhook请求
@app.route(f'/{bot_token}', methods=['POST'])
def handle_webhook_request():
    if request.method == 'POST':
        update = json.loads(request.data)
        if 'message' in update:
            handle_message(update['message'])
        return 'OK'

if __name__ == '__main__':
    # 设置Webhook
    webhook_url_full = f'{webhook_url}:{webhook_port}/{bot_token}'
    webhook_response = requests.post(f'https://api.telegram.org/bot{bot_token}/setWebhook', data={'url': webhook_url_full})
    if webhook_response.status_code != 200:
        print(f'Failed to set webhook: {webhook_response.text}')
        exit(1)

    # 启动Flask Web服务器
    app.run(host='0.0.0.0', port=webhook_port, ssl_context='adhoc')
