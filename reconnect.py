import paramiko
import telegram
from telegram.ext import Updater, CommandHandler

# 创建 SSH 客户端
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 连接到 OpenWrt 路由器
def reconnect_pppoe(bot, update):
    ssh.connect('192.168.1.1', username='root', password='password')
    _, stdout, _ = ssh.exec_command('./reconnect_pppoe.sh')
    bot.send_message(chat_id=update.message.chat_id, text=stdout.read().decode())
    _, stdout, _ = ssh.exec_command('ifconfig pppoe-wan | grep "inet\ addr" | cut -d: -f2 | awk "{print $1}"')
    ip = stdout.read().decode().strip()
    bot.send_message(chat_id=update.message.chat_id, text="当前 IP 地址：" + ip)
    ssh.close()

# 创建 Telegram 机器人
def main():
    updater = Updater(token='your_token_here')
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("reconnect", reconnect_pppoe))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
'''
请注意，您需要替换以下内容：

192.168.1.1：为 OpenWrt 路由器的 IP 地址。
username：为 OpenWrt 路由器的用户名。
password：为 OpenWrt 路由器的密码。
./reconnect_pppoe.sh：为保存重新拨号脚本的路径。
pppoe-wan：为 OpenWrt 路由器的 PPPoE 接口。
your_token_here：为您在创建 Telegram 机器人时获取的 token。
运行以上代码后，您可以通过发送 /reconnect 命令，重新拨号 OpenWrt 路由器，并在 Telegram 中显示其当前 IP 地址。
'''
