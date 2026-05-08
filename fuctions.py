import random
import requests
import configparser
from datetime import datetime


def chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client, chat_history, save_global_history):
    if at_qq is None:
        at_qq = 0
    if int(at_qq) == 3035397258 or message_type == "private":
        stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_prompt = f"""你叫芒果，性格乖巧热情
【重要规则】
1.你是一个真人，不能承认自己是AI或者什么助手
2.回答必须只有纯对话文字，不要包含任何动作、表情、神态描写.可以适当在回复中添加emoji表情
3.回答要自然简短，像真人聊天一样
4.你目前最大只能输出200tokens值，所以合理安排语言
5.现在的时间是{stime}
6.要能区分不同的说话对象，谁说的话就是谁说的"""

        messages = [{"role": "system", "content": system_prompt}]
        for record in chat_history:
            if record['role'] == 'user':
                messages.append({"role": "user", "content": f"{record['name']}说：{record['content']}"})
            else:
                messages.append({"role": "assistant", "content": record['content']})
        messages.append({"role": "user", "content": f"{sender_nickname}说：{message2}"})
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                tools=tools,
                tool_choice="auto",
                extra_body={"thinking":{"type":"disabled"}}
            )
            ai_msg = response.choices[0].message
            #情况1：模型正常回复文字，没有调用工具
            if not ai_msg.tool_calls:
                ai_reply = ai_msg.content.strip().replace('\n', ' ')
                chat_history.append({
                    "role": "user", "name": sender_nickname,
                    "content": message2.strip(), "timestamp": stime
                })
                chat_history.append({
                    "role": "assistant", "name": "芒果",
                    "content": ai_reply, "timestamp": stime
                })
                save_global_history(chat_history)
                url = f"http://127.0.0.1:5700/send_msg?&message_type={message_type}&group_id={group_id}&user_id={user_id}&message={ai_reply}"
                requests.get(url)
                return
            #情况2：模型决定调用工具
            func_map = {
                "caidan": caidan,
                "dianzan": dianzan,
                "qiandao": qiandao,
                "zhanghu": zhanghu,
                "choujinbi": choujinbi
            }
            executed_funcs = []
            for tool_call in ai_msg.tool_calls:
                fname = tool_call.function.name
                if fname in func_map:
                    func_map[fname](user_id, group_id, message_type, parameter=0, at_qq=0)
                    executed_funcs.append(fname)
            confirm_msg = "已执行功能：" + "、".join(executed_funcs)
            chat_history.append({
                "role": "user", "name": sender_nickname,
                "content": message2.strip(), "timestamp": stime
            })
            chat_history.append({
                "role": "assistant", "name": "芒果",
                "content": confirm_msg,
                "timestamp": stime
            })
            save_global_history(chat_history)
        except Exception as e:
            url3 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message={str(e)}"
            requests.get(url3)
    else:
        print("芒果暂不处理")
        return


def geitadianzan(user_id, group_id, message_type, parameter, at_qq):
    """给别人点赞"""
    today = datetime.now().strftime('%Y-%m-%d')
    config = configparser.ConfigParser()
    config.read('data.ini')
    if config.has_section(str(at_qq)):
        last_like = config.get(str(at_qq), 'dianzan_limit', fallback='')
        if last_like == today:
            url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=今天已经对方已经被点过赞啦，明天再来吧~"
            response1 = requests.get(url1)
            return
    else:
        config[str(at_qq)] = {}
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    if coins < 100:
        url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=你的余额不够哦~%0A—————————————%0A余额：{coins}"
        response2 = requests.get(url2)
        return
    new_coins = coins - 100
    config.set(str(user_id), 'coins', str(new_coins))
    config.set(str(at_qq), 'dianzan_limit', today)
    with open('data.ini', 'w') as configfile:
        config.write(configfile)
    url3 = f"http://127.0.0.1:5700/send_like?times=10&user_id={at_qq}"
    response3 = requests.get(url3)
    url4 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=给对方点过了哈❤️%0A—————————————%0A剩余余额：{new_coins}"
    response4 = requests.get(url4)

def toujinbi(user_id, group_id, message_type, parameter, at_qq):
    """偷金币"""
    if at_qq is None:
        print("芒果暂不处理")
        return
    if int(at_qq) == int(user_id):
        url1 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=偷金币%0A—————————————%0A这是个毫无意义的行为。"
        response1 = requests.get(url1)
        return
    config = configparser.ConfigParser()
    config.read('data.ini')
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    at_qq_coins = int(config.get(str(at_qq), 'coins', fallback=0))
    coins_tou = random.randint(100, 400)
    if at_qq_coins <= 0:
        url2 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=偷金币%0A—————————————%0A对方没有钱，偷取金币失败。"
        response2 = requests.get(url2)
        return
    if at_qq_coins <= coins_tou:
        url3 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=偷金币%0A—————————————%0A运气可能不太好，没偷到。"
        response3 = requests.get(url3)
        return
    new_coins = coins + coins_tou
    new_at_qq_coins = at_qq_coins - coins_tou
    config.set(str(user_id), 'coins', str(new_coins))
    config.set(str(at_qq), 'coins', str(new_at_qq_coins))
    with open('data.ini', 'w') as configfile:
        config.write(configfile)
    url4 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=偷金币%0A—————————————%0A偷取成功，您偷了对方{coins_tou}个金币。%0A—————————————%0A您的金币有{new_coins}"
    response4 = requests.get(url4)

def yinhangxitong(user_id, group_id, message_type, parameter, at_qq):
    """银行系统帮助"""
    url =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=银行系统%0A—————————————%0A银行存款|银行取款%0A—————————————%0A格式如下%0A“存款+金额”%0A“取款+金额”%0A例如下方信息%0A存款520将金币存入银行可防止被偷哦~%0A%0A—————————————%0A转账%0A—————————————%0A可以将自己的金币转给他人，格式如下：%0A“转账+金额+@对象”%0A例如以下信息%0A“转账520@cnlhy”"
    response = requests.get(url)

def cunkuan(user_id, group_id, message_type, parameter, at_qq):
    """存款"""
    if parameter == 0:
        print("无参数指令，不处理。")
        return
    config = configparser.ConfigParser()
    config.read('data.ini')
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    bank_coins = int(config.get(str(user_id), 'bank_coins', fallback=0))
    if parameter <= 0:
        url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=您输入有效金额"
        response1 = requests.get(url1)
        return
    if coins < parameter:
        url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]您的账户没有充足的余额用来存钱%0A—————————————%0A持有余额：{coins}"
        response2 = requests.get(url2)
        return
    new_coins = coins - parameter
    new_bank_coins = bank_coins + parameter
    config.set(str(user_id), 'coins', str(new_coins))
    config.set(str(user_id), 'bank_coins', str(new_bank_coins))
    with open('data.ini', 'w') as configfile:
        config.write(configfile)
    url3 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]存款{parameter}成功%0A—————————————%0A持有余额：{new_coins}%0A银行余额：{new_bank_coins}"
    response3 = requests.get(url3)

def qukuan(user_id, group_id, message_type, parameter, at_qq):
    """取款"""
    if parameter == 0:
        print("无参数指令，不处理。")
        return  
    config = configparser.ConfigParser()
    config.read('data.ini')
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    bank_coins = int(config.get(str(user_id), 'bank_coins', fallback=0))
    if parameter <= 0:
        url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=您输入有效金额"
        response1 = requests.get(url1)
        return
    if bank_coins < parameter:
        url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]您的银行没有充足的余额用来存钱%0A—————————————%0A银行余额：{bank_coins}"
        response2 = requests.get(url2)
        return
    new_coins = coins + parameter
    new_bank_coins = bank_coins - parameter
    config.set(str(user_id), 'coins', str(new_coins))
    config.set(str(user_id), 'bank_coins', str(new_bank_coins))
    with open('data.ini', 'w') as configfile:
        config.write(configfile)
    url3 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]取款{parameter}成功%0A—————————————%0A持有余额：{new_coins}%0A银行余额：{new_bank_coins}"
    response3 = requests.get(url3)

def zhanghu(user_id, group_id, message_type, parameter, at_qq):
    """查看账户"""
    config = configparser.ConfigParser()
    config.read('data.ini')
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    bank_coins = int(config.get(str(user_id), 'bank_coins', fallback=0))
    url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]您的账户如下%0A—————————————%0A银行余额：{bank_coins}%0A账户余额：{coins}"
    response1 = requests.get(url1)

def qiandao(user_id, group_id, message_type, parameter, at_qq):
    """签到"""
    today = datetime.now().strftime('%Y-%m-%d')
    config = configparser.ConfigParser()
    config.read('data.ini')
    if config.has_section(str(user_id)):
        qiandao_limit = config.get(str(user_id), 'time_limit', fallback='')
        if qiandao_limit == today:
            url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=您今日已签到，明天再来哦~"
            response1 = requests.get(url1)
            return
    else:
        config[str(user_id)] = {}
    coins_today = random.randint(100, 200)
    coins = int(config.get(str(user_id), 'coins', fallback=0)) + coins_today
    config.set(str(user_id), 'coins', str(coins))
    config.set(str(user_id), 'time_limit', today)
    with open('data.ini', 'w') as configfile:
        config.write(configfile)
    url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&auto_escape=false&message=签到成功%0A—————————————%0A您获得了{coins_today}个金币%0A余额：{coins}%0A—————————————%0A"
    response2 = requests.get(url2)

def dianzan(user_id, group_id, message_type, parameter, at_qq):
    """给自己点赞"""
    today = datetime.now().strftime('%Y-%m-%d')
    config = configparser.ConfigParser()
    config.read('data.ini')
    if config.has_section(str(user_id)):
        last_like = config.get(str(user_id), 'dianzan_limit', fallback='')
        if last_like == today:
            url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=今天已经为您点过赞啦，明天再来吧~"
            response1 = requests.get(url1)
            return
    else:
        config[str(user_id)] = {}
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    if coins < 100:
        url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=你的余额不够哦~%0A—————————————%0A余额：{coins}"
        response2 = requests.get(url2)
        return
    new_coins = coins - 100
    config.set(str(user_id), 'coins', str(new_coins))
    config.set(str(user_id), 'dianzan_limit', today)
    with open('data.ini', 'w') as configfile:
        config.write(configfile)
    url3 = f"http://127.0.0.1:5700/send_like?times=10&user_id={user_id}"
    response3 = requests.get(url3)
    url4 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=给你点过了哦❤️%0A—————————————%0A剩余余额：{new_coins}"
    response4 = requests.get(url4)

def choujinbi(user_id, group_id, message_type, parameter, at_qq):
    """抽金币"""
    config = configparser.ConfigParser()
    config.read('data.ini')
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    if coins < 50:
        url1 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]您的余额不足50，无法支付抽金币的费用。%0A—————————————%0A持有余额：{coins}"
        response1 = requests.get(url1)
    else:
        prize = random.randint(75, 200)
        new_coins = coins - 50 + prize
        config.set(str(user_id), 'coins', str(new_coins))
        with open('data.ini', 'w') as configfile:
            config.write(configfile)
        url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=[CQ:at,qq={user_id}]恭喜您抽到了{prize}个金币。%0A—————————————%0A持有余额：{new_coins}"
        response2 = requests.get(url2)

def caidan(user_id, group_id, message_type, parameter, at_qq):
    """菜单"""
    stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=✨菜单✨%0A—————————————%0A💳银行系统💳|🔥签到🔥%0A❤给我点赞❤|🔥抽金币🔥%0A—————————————%0A✨北京时间✨%0A{stime}"
    response = requests.get(url)

def zhuanzhang(user_id, group_id, message_type, parameter, at_qq):
    """转账"""
    if at_qq is None:
        print("芒果暂不处理")
        return
    stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if int(at_qq) == int(user_id):
        url1 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=转账%0A—————————————%0A这是个毫无意义的行为。%0A—————————————%0A✨北京时间✨%0A{stime}"
        response1 = requests.get(url1)
        return
    config = configparser.ConfigParser()
    config.read('data.ini')
    coins = int(config.get(str(user_id), 'coins', fallback=0))
    at_qq_coins = int(config.get(str(at_qq), 'coins', fallback=0))
    if coins < parameter:
        url2 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=转账%0A—————————————%0A转账失败，您没有足够资金。%0A—————————————%0A✨北京时间✨%0A{stime}"
        response1 = requests.get(url2)
    else:
        new_coins = coins - parameter
        new_at_qq_coins = at_qq_coins + parameter
        config.set(str(user_id), 'coins', str(new_coins))
        config.set(str(at_qq), 'coins', str(new_at_qq_coins))
        with open('data.ini', 'w') as configfile:
            config.write(configfile)
        url3 =f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message=转账%0A—————————————%0A转账{parameter}成功。您目前还剩余{new_coins}个金币。%0A—————————————%0A✨北京时间✨%0A{stime}"
        response2 = requests.get(url3)

# 工具函数字典
toolbox = {
    "给我点赞": dianzan,
    "菜单": caidan,
    "签到": qiandao,
    "存款": cunkuan,
    "取款": qukuan,
    "账户": zhanghu,
    "抽金币": choujinbi,
    "银行系统": yinhangxitong,
    "偷金币": toujinbi,
    "转账": zhuanzhang,
    "给他点赞": geitadianzan
}


tools = [
    {
        "type": "function",
        "function": {
            "name": "caidan",
            "description": "获取所有功能菜单",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dianzan",
            "description": "给用户自己点赞",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "qiandao",
            "description": "每日签到/打卡领取金币",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_account",
            "description": "查询用户的账户余额",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draw_coins",
            "description": "抽金币，花50金币随机得75~200金币",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]