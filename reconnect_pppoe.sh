#!/bin/sh

# 关闭现有的 PPPoE 拨号
ifup pppoe-wan

# 等待 5 秒
sleep 5

# 重新启动 PPPoE 拨号
ifdown pppoe-wan

# 等待 5 秒
sleep 5

# 再次启动 PPPoE 拨号
ifup pppoe-wan
