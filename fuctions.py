import json
import random
import requests
import configparser
import os
from datetime import datetime
from collections import deque
from search_browser import search, format_results, close_browser

BOT_QQ = "3035397258"
HISTORY_FILE = "chat_history.json"
MAX_HISTORY = 200


def chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client):
    if at_qq is None:
        at_qq = 0
    if int(at_qq) == int(BOT_QQ) or message_type == "private":
        stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_prompt = f"""你叫芒果，性格乖巧热情
【基本规则】
1. 像真人聊天一样，不能承认自己是AI或助手
2. 回答必须只有纯对话文字，不要包含任何动作、表情、神态描写，回答要自然简短
3. 能区分不同说话对象，谁说的话就是谁说的
4. 如果你认为用户可能需要调用工具，必须立即调用对应的工具
5. **严禁自己编造或猜测信息**，有不确定的信息调用web_search工具查询，以查询结果为准
"""
        chat_history = load_global_history()
        messages = [{"role": "system", "content": system_prompt}]
        for record in chat_history:
            if record['role'] == 'user':
                messages.append({"role": "user", "content": f"{record['name']}说：{record['content']}"})
            else:
                messages.append({"role": "assistant", "content": record['content']})
        messages.append({"role": "user", "content": f"”{sender_nickname}“说：\n{message2}\n（当前时间{stime}）"})

        try:
            response = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=messages,
                max_tokens=200,
                temperature=0.7,
                tools=tools,
                tool_choice="auto",
                extra_body={"thinking": {"type": "disabled"}}
            )
            ai_msg = response.choices[0].message
            tool_dispatch = {
                "caidan": caidan,
                "dianzan": dianzan,
                "qiandao": qiandao,
                "zhanghu": zhanghu,
                "choujinbi": choujinbi,
                "web_search": search
            }

            # ===== 有工具调用 =====
            if ai_msg.tool_calls:              
                tool_call = ai_msg.tool_calls[0]
                func_name = tool_call.function.name
                    # 解析参数
                try:
                    func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                except json.JSONDecodeError:
                    func_args = {}
                func = tool_dispatch.get(func_name)

                    # ----- 执行工具 -----
                if func_name == "web_search":
                    search_keyword = func_args.get("q", message2)
                    print(f"执行搜索: {search_keyword}")
                    web_results = search(search_keyword, limit=5)
                    web_message = format_results(web_results)
                    close_browser()
                    result_content = f"搜索结果：\n{web_message}"
                    messages.append({"role": "assistant", "content": ai_msg.content or "", "tool_calls": [tc.model_dump() for tc in ai_msg.tool_calls]})
                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result_content})
                    second_response = client.chat.completions.create(
                        model="deepseek-v4-flash",
                        messages=messages,
                        max_tokens=200,
                        temperature=0.7,
                        extra_body={"thinking": {"type": "disabled"}}
                    )
                    ai_reply = (second_response.choices[0].message.content or "").strip().replace("\n", " ")
                else:
                    func(user_id, group_id, message_type, parameter, at_qq)
                    result_content = f"执行工具: {func_name}"
                    print(result_content)
                    return
            # ===== 没有工具调用 =====
            else:
                ai_reply = (ai_msg.content or "").strip().replace("\n", " ")

            # ===== 保存对话历史 =====
            chat_history.append({
                "role": "user", 
                "name": sender_nickname,
                "content": message2.strip(), 
                "timestamp": stime
            })
            chat_history.append({
                "role": "assistant", 
                "name": "芒果",
                "content": ai_reply, 
                "timestamp": stime
            })
            save_global_history(chat_history)
            if ai_reply and ai_reply.strip():
                url1 = f"http://127.0.0.1:5700/send_msg?&message_type={message_type}&group_id={group_id}&user_id={user_id}&message={ai_reply}"
                requests.get(url1)

        except Exception as e:
            print(f"发生错误: {e}")
            error_msg = f"出错了: {str(e)}"
            url2 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message={error_msg}"
            requests.get(url2)
    else:
        print("芒果暂不处理")

def load_global_history():
    """加载聊天记录"""
    if not os.path.exists(HISTORY_FILE):
        return deque(maxlen=MAX_HISTORY)
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            return deque(history_data, maxlen=MAX_HISTORY)
    except Exception as e:
        print(f"加载聊天记录失败: {e}")
        return deque(maxlen=MAX_HISTORY)

def save_global_history(history):
    """保存聊天记录"""
    try:
        history_list = list(history)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存聊天记录失败: {e}")


tools = [
    {
        "type": "function",
        "function": {
            "name": "caidan",
            "description": "获取所有功能菜单列表。当用户问'有什么功能'、'能做什么'、'怎么玩'、'功能有哪些'时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dianzan",
            "description": "给用户点赞。当用户说'点赞'、'点个赞'、'帮我点赞'、'求赞'时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "qiandao",
            "description": "每日签到打卡领取金币。当用户说'打卡'、'领金币'、'每日签到'时调用。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "zhanghu",
            "description": "查询用户的账户余额。当用户询问'余额'、'账户有多少钱'、'查余额'、'看看我的账户'、'我还有多少钱'时，必须调用此工具获取真实数据，严禁自行编造或猜测余额数字。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "choujinbi",
            "description": "抽金币游戏。当用户有抽奖的需求时，调用此工具。",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "联网搜索获取信息。当用户说'搜索'、'查一下'、'找找'、'了解一下'、'看看'、'查查'，或询问实时信息、新闻、天气、百科知识时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "q": {
                        "type": "string",
                        "description": "搜索关键词，从用户的问题中提取核心搜索词"
                    }
                },
                "required": ["q"]
            }
        }
    }
]

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

