import asyncio
import datetime
import json
import logging
import os
import re
import time
from urllib import parse

from cacheout import FIFOCache
from telethon import TelegramClient, events

# 0. 进入容器
# 0. docker exec -it qinglong bash
# 1. pip3 install -U cacheout
# 2. 复制magic.py,magic.json到/ql/config/目录 并配置
# 3. python3 /ql/config/magic.py 用手机号登录
# 4. 给bot发送在吗 有反应即可
# 5. pm2 start /ql/config/magic.py -x --interpreter python3
# 6. 挂起bot到后台 查看状态 pm2 l
# 7. 如果修改了magic.json,执行pm2 restart magic 即可重启

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)
# 创建
logger = logging.getLogger("magic")
logger.setLevel(logging.INFO)

_ConfigCar = ""
_ConfigSh = ""
if os.path.exists("/jd/config/magic.json"):
    _ConfigCar = "/jd/config/magic.json"
    _ConfigSh = "/jd/config/config.sh"
elif os.path.exists("/ql/config/magic.json"):
    _ConfigCar = "/ql/config/magic.json"
    _ConfigSh = "/ql/config/config.sh"
elif os.path.exists("/ql/data/config/magic.json"):
    _ConfigCar = "/ql/data/config/magic.json"
    _ConfigSh = "/ql/data/config/config.sh"
else:
    logger.info("未找到magic.json config.sh")

with open(_ConfigCar, 'r', encoding='utf-8') as f:
    magic_json = f.read()
    properties = json.loads(magic_json)

# 缓存
cache = FIFOCache(maxsize=properties.get("monitor_cache_size"), ttl=0, timer=time.time)

# Telegram相关
api_id = properties.get("api_id")
api_hash = properties.get("api_hash")
bot_id = properties.get("bot_id")
bot_token = properties.get("bot_token")
user_id = properties.get("user_id")
# 监控相关
log_path = properties.get("log_path")
log_send = properties.get("log_send", True)
log_send_id = properties.get("log_send_id")
monitor_cars = properties.get("monitor_cars")
logger.info(f"监控的频道或群组-->{monitor_cars}")
monitor_converters = properties.get("monitor_converters")
logger.info(f"监控转换器-->{monitor_converters}")
monitor_converters_whitelist_keywords = properties.get("monitor_converters_whitelist_keywords")
logger.info(f"不转换白名单关键字-->{monitor_converters_whitelist_keywords}")
monitor_black_keywords = properties.get("monitor_black_keywords")
logger.info(f"黑名单关键字-->{monitor_black_keywords}")
monitor_scripts = properties.get("monitor_scripts")
monitor_auto_stops = properties.get("monitor_auto_stops")
logger.info(f"监控的自动停车-->{monitor_auto_stops}")
rules = properties.get("rules")
logger.info(f"监控的自动解析-->{monitor_auto_stops}")

if properties.get("proxy"):
    if properties.get("proxy_type") == "MTProxy":
        proxy = {
            'addr': properties.get("proxy_addr"),
            'port': properties.get("proxy_port"),
            'proxy_secret': properties.get('proxy_secret', "")
        }
    else:
        proxy = {
            'proxy_type': properties.get("proxy_type"),
            'addr': properties.get("proxy_addr"),
            'port': properties.get("proxy_port"),
            'username': properties.get('proxy_username', ""),
            'password': properties.get('proxy_password', "")
        }
    client = TelegramClient("magic", api_id, api_hash, proxy=proxy, auto_reconnect=True, retry_delay=1, connection_retries=99999).start()
else:
    client = TelegramClient("magic", api_id, api_hash, auto_reconnect=True, retry_delay=1, connection_retries=99999).start()


def rest_of_day():
    """
    :return: 截止到目前当日剩余时间
    """
    today = datetime.datetime.strptime(str(datetime.date.today()), "%Y-%m-%d")
    tomorrow = today + datetime.timedelta(days=1)
    nowTime = datetime.datetime.now()
    return (tomorrow - nowTime).seconds - 90  # 获取秒


def rwcon(arg):
    if arg == "str":
        with open(_ConfigSh, 'r', encoding='utf-8') as f1:
            configs = f1.read()
        return configs
    elif arg == "list":
        with open(_ConfigSh, 'r', encoding='utf-8') as f1:
            configs = f1.readlines()
        return configs
    elif isinstance(arg, str):
        with open(_ConfigSh, 'w', encoding='utf-8') as f1:
            f1.write(arg)
    elif isinstance(arg, list):
        with open(_ConfigSh, 'w', encoding='utf-8') as f1:
            f1.write("".join(arg))


async def export(text):
    messages = text.split("\n")
    change = ""
    key = ""

    for message in messages:
        if "export " not in message:
            continue
        kv = message.replace("export ", "")
        key = kv.split("=")[0]
        value = re.findall(r'"([^"]*)"', kv)[0]
        configs = rwcon("str")
        if kv in configs:
            continue
        if key in configs:
            configs = re.sub(f'{key}=("|\').*("|\')', kv, configs)
            change += f"\n【执行替换】环境变量成功\n{kv}"
            await client.send_message(bot_id, change)
        else:
            end_line = 0
            configs = rwcon("list")
            for config in configs:
                if "第二区域" in config and "↑" in config:
                    end_line = configs.index(config)
                    # await client.send_message(bot_id, f'结束行数>>> \n{end_line}')
                    break
            configs.insert(end_line, f'export {key}="{value}"\n')
            change += f"\n【执行新增】环境变量成功\n{kv}"
            await client.send_message(bot_id, change)
        rwcon(configs)
    if len(change) == 0:
        await client.send_message(bot_id, f'【取消替换】变量无需修改\n{kv}')


# 设置变量
@client.on(events.NewMessage(chats=[bot_id], pattern='^没水了$'))
async def handler(event):
    for auto_stop_file in monitor_auto_stops:
        os.popen(f"ps -ef | grep {auto_stop_file}" + " | grep -v grep | awk '{print $1}' | xargs kill -9")
    await client.send_message(bot_id, f'Magic监控发现{auto_stop_file}没水停车')


# 设置变量
@client.on(events.NewMessage(chats=[bot_id], pattern='^(magic 重启|magic cq)$'))
async def handler(event):
    await client.send_message(bot_id, f'Magic监控开始重启，稍后发送magic确认是否启动')
    os.system('pm2 restart magic')


# 设置变量
@client.on(events.NewMessage(chats=[bot_id], pattern='^magic$'))
async def handler(event):
    await client.send_message(bot_id, f'Magic监控运行中！')


# 提取多行转换
async def converter_lines(text):
    before_eps = text.split("\n")
    after_eps = [elem for elem in before_eps if elem.startswith("export")]
    return await converter_handler("\n".join(after_eps))


# 设置变量
@client.on(events.NewMessage(from_users=[user_id], pattern='^(run|Run)$'))
async def handler(event):
    groupname = "mybot"
    try:
        groupname = f'[{event.chat.title}](https://t.me/c/{event.chat.id}/{event.message.id})'
    except Exception:
        pass

    reply = await event.get_reply_message()
    reply_text = reply.text

    separator = '"' #最后出现之后的字符过滤掉
    reply_text = reply_text.rsplit(separator, 1)[0] + separator #最后出现之后的字符过滤掉

    # 提取变量
    if "export" in reply_text:
        strindex = reply_text.find('export')  # 0则是第一个export前面没有其他字符  大于0则是有其他不正确字符 需要处理
        if strindex > 0: # 判断export字符前面是否有其他文字，没有 结果是0 ， 有需要过滤的字符 返回结果大于0
            reply_text = reply_text[reply_text.find('export'):]
        reply_text = await converter_handler(reply_text)  #先根据变量转换规则对变量进行变量转换

        # await client.send_message(bot_id, f'变量名前有非法字符 需要处理，处理后\n{reply_text}')
        kv = reply_text.replace("export ", "")
        key = reply_text.split("=")[0]
        # url活动  用链接去匹配，防止出现转链的形似 多个https的情况，一下是取最后一个https的内容取转变量
        if "https" in reply_text:
            httplst = reply_text[ reply_text.rindex( 'https' ) : len( reply_text ) ]
            httplst = httplst.replace('"','') #去除双引号
            # await client.send_message(bot_id, f'变量名前有非法字符 需要处理，处理后\n{httplst}')
            reply_text = key + "=" + '"' + httplst + '"'
        activity_id, url = await get_activity_info(reply_text)
    else:
        activity_id, url = await get_activity_info(reply_text) #先去处理一遍 看看是否为正确的数据
        #await client.send_message(bot_id, f'RUN命令-群/频道\n测试 reply_text>>>>>1111\n{reply_text}\n{activity_id}\n{url}')
        if activity_id is None: #先以url形式取获取id，不能获取到id，再去判断数据的具体形式
            if "=" in reply_text:  # 如果在字符串中没有https 就加上再去处理  一些老六故意不写
                if "\n" in reply_text:
                    # await client.send_message(bot_id, f'RUN命令-群/频道\nid为空 数据继续处理  前>>>>>2222\n{reply_text}\n{activity_id}\n{url}')
                    textindex = reply_text.rfind("\n") #返回最右边（最后一次）字符的位置
                    reply_text = reply_text[textindex:]
                    reply_text = reply_text.replace('\n','')
                    if " " in reply_text:
                        textindex = reply_text.rfind(" ") #返回最右边（最后一次）字符的位置
                        reply_text = reply_text[textindex:]
                        reply_text = reply_text.replace(' ','')
                    if "https" not in reply_text: #继续判断是否是不带https标识的链接
                        if "/" in reply_text:
                            reply_text = "https://" + reply_text
                        else:
                            reply_text = "export " + reply_text
                    #activity_id, url = await get_activity_info(reply_text) #经过数据处理 如果id url还是空 说明是非url的id形式变量
                elif " " in reply_text: # 非url的id形式变量 例如 大牌联合 DPLHTY="xxxxx" 这种没有export 变量名前还有文字 空格的
                    textindex = reply_text.rfind(" ") #返回最右边（最后一次）字符的位置
                    reply_text = reply_text[textindex:]
                    reply_text = reply_text.replace(' ','')
                    if "https" not in reply_text: #继续判断是否是不带https标识的链接
                        if "/" in reply_text:
                            reply_text = "https://" + reply_text
                        else:
                            reply_text = "export " + reply_text
                    #activity_id, url = await get_activity_info(reply_text) #经过数据处理 如果id url还是空 说明是非url的id形式变量
                elif "https" not in reply_text: #继续判断是否是不带https标识的链接
                    if "/" in reply_text:
                        reply_text = "https://" + reply_text
                    else:
                        reply_text = "export " + reply_text
                activity_id, url = await get_activity_info(reply_text) #经过数据处理 如果id url还是空 说明是非url的id形式变量
                reply_text = await converter_handler(reply_text)  #先根据变量转换规则对变量进行变量转换
    #await client.send_message(bot_id, f'RUN命令-没有自动车变量形式【{groupname}】群/频道\n<--⚠URL活动变量⚠-->链接缺少id参数。\n{reply_text}')
    if url is not None:
        action = None #用变量名取查找是否配置
        if activity_id is None and "M_FANS_RED_PACKET_URL" not in reply_text:
            logger.info(f"未找到id [%s],退出", url)
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令<--⚠URL活动变量⚠-->链接缺少id参数。\n{kv}')
            return
        is_break = False
        for rule_key in rules:
            if is_break:
                break
            result = re.search(rule_key, url)
            # 如果没有可匹配的就会报错，说明该变量的名既没有预设，而且url也是没有预设的，请检查
            if result is None:
                logger.info(f"不匹配%s,下一个", rule_key)
                continue
            value = rules.get(rule_key)
            env = value.get("env")
            argv_len = len(re.findall("%s", env))
            env_key = re.findall("export (.*)=", env)[0]
            if argv_len == 1:
                env = env % url
            elif argv_len == 2:
                env = env % (activity_id, url)
                envs = env.split("\n")[0]
                env = envs
            elif argv_len == 3:
                domain = re.search('(https?://[^/]+)', url)[0]
                env = env % (activity_id, domain, "None")
            else:
                await client.send_message(bot_id, f'【{groupname}】群/频道\n该变量属于⚠URL规则参数配置不正确的活动⚠，是正常活动请手动完善JSON规则！\n{kv}')
                return
            reply_text = env
            kv = reply_text.replace("export ", "")
            key = kv.split("=")[0]
            action = monitor_scripts.get(key)
        if action is None:
            if "export" in reply_text:
                kv = reply_text.replace("export ", "")
                await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令<--⚠不符合Rules规则⚠-->的链接变量,请确认该链接是否有效。\n{kv}')
            else:
                await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令<--⚠不符合Rules规则⚠-->的链接,请确认该链接是否有效。\n{reply_text}')
            return
    else:
        reply_text = await converter_handler(reply_text)  #先根据变量转换规则对变量进行变量转换
        kv = reply_text.replace("export ", "")
        key = kv.split("=")[0]
        action = monitor_scripts.get(key)
        if action is None:
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令<--⚠非麦基监控⚠-->变量,请确认该变量是否有效\n{kv}')
        name = action.get("name")
        activityid = kv.split("=")[1] # 取id格式变量值  #activityid为空的情况下判断url是否为空，如果url是none，说明该变量是个id形式变量，直接取id值
        activity_id = activityid.replace('"','')
        if len(activity_id)==0:  # 识别变量值为""空的情况
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令 {name} 任务的变量⚠空值⚠，跳过不执行\n{kv}')
            return
        if len(activity_id) < 5:  # 识别变量值为""空的情况
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令 {name} 任务的变量⚠ID长度非法⚠，跳过不执行\n{kv}')
            return

    #await client.send_message(bot_id, f'RUN命令-群/频道\nURL 直接run 数据继续处理  后>>>>>3333\n{action}\n{reply_text}\n{activity_id}\n{url}')

    try:
        if event.is_reply is False:
            await client.send_message(bot_id, f'abc')
            return
        await event.delete()
        kv = reply_text.replace("export ", "")
        #key = kv.split("=")[0]
        name = action.get("name")
        # 没有匹配的动作 或没开启
        if not action.get("enable"):
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令 {name} ⚠任务设置不启动⚠，启用设置enable的值：false--->true并重启Magic\n{kv}')
            return
        command = action.get("task", "")
        if command == '':
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令 {name} 任务未配置对应脚本\n{kv}')
            return
        if cache.get(activity_id) is not None:
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令已跑过的 {name} 任务变量再次执行\n{kv}')
        else:
            await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令全新的 {name} 任务变量立即执行并加入缓存\n{kv}')
            cache.set(activity_id, activity_id, rest_of_day())
        await export(reply_text)
        await cmd(command)
        return
    except Exception as e:
       # logger.error(e)
        await client.send_message(bot_id, f'【{groupname}】群/频道\nRun命令⚠该变量属于😟变量名以及URL都无法匹配的魔法变量😟找到源头打他一顿⚠\n{reply_text}')


# 设置变量
@client.on(events.NewMessage(chats=[bot_id], pattern='^(magic 清理|magic 清空|magic qk)$'))
async def handler(event):
    b_size = cache.size()
    logger.info(f"清理前缓存数量，{b_size}")
    cache.clear()
    a_size = cache.size()
    logger.info(f"清理后缓存数量，{a_size}")
    await client.send_message(bot_id, f'Magic监控清理缓存结束 {b_size}-->{a_size}')


async def get_activity_info(text):
    result = re.findall(r'((http|https)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|])', text)
    logger.info(result)

    if len(result) <= 0:
        return None, None
    url = re.search('((http|https)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|])', text)[0]
    logger.info(url)

    params = parse.parse_qs(parse.urlparse(url).query)
    logger.info(params)

    ban_rule_list = [
        'activityId',
        'shopId',
        'giftId',
        'actId',
        'tplId',
        'token',
        'code',
        'a',
        'id']
    activity_id = ''
    for key in ban_rule_list:
        activity_id = params.get(key)
        logger.info(activity_id)
        if activity_id is not None:
            activity_id = params.get(key)
            activity_id = activity_id[0]
            break
    return activity_id, url


@client.on(events.NewMessage(chats=monitor_cars, pattern=r'(([\s\S]*)export\s?\w*=(".*"|\'.*\')([\s\S]*)|[/ikun])'))
async def handler(event):
    origin = event.message.text
    text = re.findall(r'https://i.walle.com/api\?data=(.+)?\)', origin)
    if len(text) > 0:
        text = parse.unquote_plus(text[0])
    elif "export" in origin:
        text = origin
    else:
        return
    try:
        groupname = f'[{event.chat.title}](https://t.me/c/{event.chat.id}/{event.message.id})'
    except Exception:
        groupname = "我的机器人Bot"
        pass
    strindex =text.find('export')  # 0则是export前面没有其他字符  大于0则是有其他不正确字符 需要处理
    if strindex > 0: # export在首位时 index为0  不是首位就是大于0的值
        # 以下两行是遇到export前面有其他字符的情况，输出export以及之后的字符
        text = text[text.find('export'):]
    separator = '"' #最后出现之后的字符过滤掉
    text = text.rsplit(separator, 1)[0] + separator
    try:
        origin_text = text
        logger.info(f"原始数据 {origin_text}")
        # 黑名单
        for b_key in monitor_black_keywords:
            result = re.search(b_key, origin_text)
            if result is not None:
                await client.send_message(bot_id, f'1触发Magic监控黑名单 {b_key} {text}')
                return
        kv = text.replace("export ", "")
        key = text.split("=")[0]
        if "https" in text: #url活动  用链接去匹配，防止出现转链的形似 多个https的情况，一下是取最后一个https的内容取转变量
            httplst = text[ text.rindex( 'https' ) : len( text ) ]
            httplst = httplst.replace('"','') #去除双引号
            text = key + "=" + '"' + httplst + '"'
        text = await converter_handler(text)  #先根据变量转换规则对变量进行变量转换
        activity_id, url = await get_activity_info(text)
        if groupname is not None:
            if activity_id is not None:  # 正确的url会提取到id 如果id空说明url错误或者是个id变量
                logger.info(f"获取到变量id：%s,继续", activity_id)
                if cache.get(activity_id) is not None:
                    logger.info(f"该变量在缓存中找到，继续")
                    key = kv.split("=")[0] #取变量名
                    if url is not None:  # 没有自动车
                        action = None
                        is_break = False
                        for rule_key in rules:
                            if is_break:
                                break
                            result = re.search(rule_key, url)
                            # 如果没有可匹配的就会报错，说明该变量的名既没有预设，而且url也是没有预设的，请检查
                            if result is None:
                                logger.info(f"RuleKey不匹配%s,下一个", rule_key)
                                continue
                            value = rules.get(rule_key)
                            env = value.get("env")
                            argv_len = len(re.findall("%s", env))
                            env_key = re.findall("export (.*)=", env)[0]
                            if argv_len == 1:
                                env = env % url
                            elif argv_len == 2:
                                env = env % (activity_id, url)
                                envs = env.split("\n")[0]
                                env = envs
                            elif argv_len == 3:
                                domain = re.search('(https?://[^/]+)', url)[0]
                                env = env % (activity_id, domain, "None")
                            else:
                                logger.info("还不支持")
                                await client.send_message(bot_id, f'15【{groupname}】\n监控到<--⚠没有匹配规则⚠-->Url格式变量，请确认是否完善规则\n{text}')
                                return
                            text = env
                            kv = text.replace("export ", "")
                            key = kv.split("=")[0]
                            action = monitor_scripts.get(key)
                            if action is None:
                                await client.send_message(bot_id, f'3【{groupname}】\nAction是空 不执行 请检查！！！\n{kv}')
                                return
                            name = action.get("name")
                            await client.send_message(bot_id, f'【{groupname}】\n监控到 {name} 任务⚠重复⚠变量，跳过不执行\n{kv}')
                            return
                        if action is None:
                            await client.send_message(bot_id, f'【{groupname}】\n监控到⚠重复⚠非麦基监控的链接变量<--⚠不符合Rules规则⚠-->,请确认该链接是否有效。\n{kv}')
                            return
                    else:
                        name = action.get("name")
                        await client.send_message(bot_id, f'【{groupname}】\n监控到 {name} 任务的⚠重复⚠变量，跳过不执行\n{kv}')
                        return
                else:  #全新的
                    key = kv.split("=")[0] #取变量名
                    if url is not None:  # 没有自动车
                        action = None
                        is_break = False
                        for rule_key in rules:
                            if is_break:
                                break
                            result = re.search(rule_key, url)
                            # 如果没有可匹配的就会报错，说明该变量的名既没有预设，而且url也是没有预设的，请检查
                            if result is None:
                                logger.info(f"RuleKey不匹配%s,下一个", rule_key)
                                continue
                            value = rules.get(rule_key)
                            env = value.get("env")
                            argv_len = len(re.findall("%s", env))
                            env_key = re.findall("export (.*)=", env)[0]
                            if argv_len == 1:
                                env = env % url
                            elif argv_len == 2:
                                env = env % (activity_id, url)
                                envs = env.split("\n")[0]
                                env = envs
                            elif argv_len == 3:
                                domain = re.search('(https?://[^/]+)', url)[0]
                                env = env % (activity_id, domain, "None")
                            else:
                                logger.info("还不支持")
                                await client.send_message(bot_id, f'15【{groupname}】\n监控到<--⚠没有匹配规则⚠-->Url格式变量，请确认是否完善规则\n{text}')
                                return
                            text = env
                            kv = text.replace("export ", "")
                            key = kv.split("=")[0]
                            action = monitor_scripts.get(key)
                            logger.info(f"添加%s到缓存", activity_id)
                            cache.set(activity_id, activity_id, rest_of_day())
                        if action is None:
                            await client.send_message(bot_id, f'【{groupname}】\n监控到非麦基监控的链接变量<--⚠不符合Rules规则⚠-->,请确认该链接是否有效。\n{kv}')
                            cache.set(activity_id, activity_id, rest_of_day())
                            return
                    else:
                        logger.info(f"添加%s到缓存", activity_id)
                        cache.set(activity_id, activity_id, rest_of_day())
            else:
                kv = text.replace("export ", "")
                activityid = kv.split("=")[1] #取id格式变量值  #activityid为空的情况下判断url是否为空，如果url是none，说明该变量是个id形式变量，直接取id值
                activity_id = activityid.replace('"','') #去除双引号
                key = kv.split("=")[0]
                if url is not None and "M_FANS_RED_PACKET_URL" not in text:  # activityid为空的情况下判断url是否为空，如果url不是none
                    await client.send_message(bot_id, f'【{groupname}】\n监控到非麦基监控<--⚠URL活动变量⚠-->\n{kv}')
                    return
                action = monitor_scripts.get(key)
                if action is not None:
                    if len(activity_id)==0:
                        name = action.get("name")
                        await client.send_message(bot_id, f'【{groupname}】\n监控到 {name} 任务的变量⚠空值⚠，跳过不执行\n{kv}')
                        return
                    if len(activity_id) < 5:
                        name = action.get("name")
                        await client.send_message(bot_id, f'【{groupname}】\n监控到 {name} 任务的变量⚠ID长度非法⚠，跳过不执行\n{kv}')
                        return
                    if cache.get(activity_id) is not None:
                        name = action.get("name")
                        await client.send_message(bot_id, f'【{groupname}】\n监控到 {name} 任务的⚠重复⚠变量，跳过不执行\n{kv}')
                        return
                    else: #缓存中没用找到 新变量添加到缓存
                        logger.info(f"添加%s到缓存", activity_id)
                        cache.set(activity_id, activity_id, rest_of_day())
                else:
                    if cache.get(activity_id) is not None:
                        await client.send_message(bot_id, f'【{groupname}】\n监控到⚠重复⚠<--非麦基监控变量-->，自行确认是否添加到监控\n{kv}')
                        return
                    else:
                        await client.send_message(bot_id, f'【{groupname}】\n监控到<--⚠非麦基监控变量⚠-->\n{kv}')
                        cache.set(activity_id, activity_id, rest_of_day())
                        return
                if len(activity_id)==0:
                    await client.send_message(bot_id, f'14没有自动车【{groupname}】\n监控到未知空值活动变量\n{kv}')
                    return
                elif len(activity_id) < 5:
                    await client.send_message(bot_id, f'14没有自动车【{groupname}】\n监控到<--⚠ID长度非法-->⚠活动变量\n{kv}')
                    return
        logger.info(f"最终变量 {text}")
        kv = text.replace("export ", "")
        #key = kv.split("=")[0]
        name = action.get("name")
        if not action.get("enable"):
            logger.info("判断任务是否启动 false不跑")
            await client.send_message(bot_id, f'【{groupname}】\n{name} 任务<--⚠未开启监控⚠-->，启用设置enable的值：false--->true并重启Magic\n{kv}')
            return
        command = action.get("task", "")
        if command == '':
            await client.send_message(bot_id, f'30【{groupname}】\n{name} 任务<--⚠未配置对应脚本⚠-->\n{kv}')
            return
        if action.get("queue"):
            await client.send_message(bot_id, f'【{groupname}】\n{name} 任务变量加入队列\n{kv}')
            await queues[action.get("queue_name")].put({"text": text, "groupname": groupname, "action": action})
            return
        await client.send_message(bot_id, f'【{groupname}】\n{name} 任务变量立即执行\n{kv}')
        await export(text)
        await cmd(command)
        return
    except Exception as e:
        logger.error(e)
        # await client.send_message(bot_id, f'傻子变量{str(e)}')
        await client.send_message(bot_id, f'33【{groupname}】\n监控到<--⚠无法处理⚠-->的数据导致程序出错，自行检查过滤数据⚠\n{kv}\n{str(e)}')



async def converter_handler(text):
    text = "\n".join(list(filter(lambda x: "export " in x, text.replace("`", "").split("\n"))))
    for c_w_key in monitor_converters_whitelist_keywords:
        result = re.search(c_w_key, text)
        if result is not None:
            logger.info(f"c_w_key无需转换 {c_w_key}")
            logger.info(f"result无需转换 {result}")
            logger.info(f"无需转换 {text}")
            return text
    logger.info(f"转换前数据 {text}")
    try:
        tmp_text = text
        logger.info(f"测试-------tmp_text数值%s", tmp_text)
        #await client.send_message(bot_id, f'数据  ----\n{tmp_text}')
        # 转换
        for c_key in monitor_converters:
            result = re.search(c_key, text)
            if result is None:
                logger.info(f"规则不匹配 {c_key},下一个")
                continue
            rule = monitor_converters.get(c_key)
            target = rule.get("env")
            argv_len = len(re.findall("%s", target))
            #await client.send_message(bot_id, f'数据参数个数  ----\n{argv_len}')
            values = re.findall(r'"([^"]*)"', text)
            #await client.send_message(bot_id, f'values数据 ----\n{values}')
            logger.info(f"测试-----argv_len数值%s", argv_len)
            if argv_len == 1:
                target = target % (values[0])
            elif argv_len == 2:
                activity_id, url = await get_activity_info(text)

                target = target % (activity_id, url)
                #await client.send_message(bot_id, f'target数据 ----\n{target}')
                logger.info(f"两个变量组合{target}")
            elif argv_len == 3:
                target = target % (values[0], values[1], values[2])
            else:
                print("不支持更多参数")
            text = target
            #await client.send_message(bot_id, f'转换数据-----\n{text}')
            logger.info(f"测试-------text数值%s", text)
            break
        tmp_text = text.split("\n")[0]
        text = tmp_text
       # logger.info(f"测试----222---text数值%s", text)
    except Exception as e:
        logger.info(str(e))
    logger.info(f"转换后数据 {text}")
    return text


queues = {}


async def task(task_name, task_key):
    logger.info(f"队列监听--> {task_name} {task_key} 已启动，等待任务")
    curr_queue = queues[task_key]
    while True:
        try:
            param = await curr_queue.get()
            logger.info(f"出队执行 {param}")
            exec_action = param.get("action")
            text = param.get("text")
            # await client.send_message(bot_id, f'【{param.get("groupname")}】\n{exec_action.get("name")} 出队执行\n{text}')

            kv = text.replace("export ", "")
            # 默认立马执行
            await client.send_message(bot_id, f'【{param.get("groupname")}】\n{exec_action.get("name")} 出队执行\n{kv}')
            await export(text)
            await cmd(exec_action.get("task", ""))
            if curr_queue.qsize() > 1:
                exec_action = param.get("action")
                await client.send_message(bot_id, f'【{exec_action["name"]}】\n排队长度{curr_queue.qsize()}，活动切换预设间隔{exec_action["wait"]}秒执行')
                await asyncio.sleep(exec_action['wait'])
        except Exception as e:
            logger.error(e)


async def cmd(exec_cmd):
    try:
        logger.info(f'执行命令 {exec_cmd}')
        name = re.findall(r'(?:.*/)*([^. ]+)\.(?:js|py|sh)', exec_cmd)[0]
        tmp_log = f'{log_path}/{name}.{datetime.datetime.now().strftime("%H%M%S%f")}.log'
        logger.info(f'日志文件 {tmp_log}')
        proc = await asyncio.create_subprocess_shell(
            f"{exec_cmd} >> {tmp_log} 2>&1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if log_send:
            await client.send_file(log_send_id, tmp_log)
            os.remove(tmp_log)
    except Exception as e:
        logger.error(e)
        await client.send_message(bot_id, f'抱歉，遇到未知错误！\n{str(e)}')


if __name__ == "__main__":
    try:
        logger.info("开始运行")
        for key in monitor_scripts:
            action = monitor_scripts[key]
            name = action.get('name')
            queue = action.get("queue")
            queue_name = action.get("queue_name")
            if queues.get(queue_name) is not None:
                logger.info(f"队列监听--> {name} {queue_name} 已启动，等待任务")
                continue
            queues[queue_name] = asyncio.Queue()
            client.loop.create_task(task(name, queue_name))
        client.run_until_disconnected()
    except Exception as e:
        logger.error(e)
        client.disconnect()