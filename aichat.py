from flask import Flask, request # type: ignore
import requests
import os
import json
import re
from collections import deque
from datetime import datetime
from openai import OpenAI # type: ignore
from fuctions import toolbox

app = Flask(__name__)

# 初始化 OpenAI 客户端
api_key = os.getenv('AIKEY')
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# 全局聊天记录文件
HISTORY_FILE = "chat_history.json"
MAX_HISTORY = 200

def load_global_history():
    """加载全局聊天记录"""
    if not os.path.exists(HISTORY_FILE):
        return deque(maxlen=MAX_HISTORY)
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            print(f"已加载聊天记录，共 {len(history_data)} 条记录")
            return deque(history_data, maxlen=MAX_HISTORY)
    except Exception as e:
        print(f"加载聊天记录失败: {e}")
        return deque(maxlen=MAX_HISTORY)

def save_global_history(history):
    """保存全局聊天记录"""
    try:
        history_list = list(history)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存聊天记录失败: {e}")

# 全局聊天记录
chat_history = load_global_history()

def chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client, chat_history, save_global_history):
    """聊天功能"""
    if at_qq is None:
        at_qq = 0
    if int(at_qq) == 3035397258 or message_type == "private":
        stime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_prompt = f"""你叫芒果，性格乖巧热情
【重要规则】
1. 你是一个真人，不是AI助手
2. 回答必须只有纯对话文字，不要包含任何动作、表情、神态描写
3. 回答要自然简短，像真人聊天一样
4. 你目前最大只能输出200tokens值，所以合理安排语言
5. 现在的时间是{stime}
6. 你必须清楚记住每个人说的话，不能把不同用户的信息搞混
7. 要能区分不同的说话对象，谁说的话就是谁说的"""
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史记录（每条记录单独作为一条消息）
        for record in chat_history:
            if record['role'] == 'user':
                # 用户消息，带上用户名
                messages.append({"role": "user", "content": f"{record['name']}说：{record['content']}"})
            else:
                # 机器人消息
                messages.append({"role": "assistant", "content": record['content']})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": f"{sender_nickname}说：{message2}"})
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-flash", 
                messages=messages, 
                max_tokens=200, 
                temperature=0.5, 
                extra_body={"thinking":{"type":"disabled"}}
            )
            ai_reply = response.choices[0].message.content.strip().replace('\n', ' ')
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
            url2 = f"http://127.0.0.1:5700/send_msg?&message_type={message_type}&group_id={group_id}&user_id={user_id}&message={ai_reply}"
            response = requests.get(url2)
        except Exception as e:
            url3 = f"http://127.0.0.1:5700/send_msg?message_type={message_type}&group_id={group_id}&user_id={user_id}&message={str(e)}"
            response = requests.get(url3)
    else:
        print("芒果暂不处理")
        return

@app.route('/', methods=['POST'])
def post_data():
    data = request.get_json(force=True)
    post_type = data.get('post_type')
    flag = data.get('flag')
    message_type = data.get('message_type')
    user_id = data.get('user_id')
    group_id = data.get('group_id')
    message1 = data.get('message', [])
    sender_nickname = data.get('sender', {}).get('nickname')
    if post_type == "request":
        url = f"http://127.0.0.1:5700/set_friend_add_request?flag={flag}&approve=true"
        requests.get(url)
        print("同意了用户（", user_id, "）的好友请求")
        return "_"
    at_qq = None
    for item in message1:
        if item.get('type') == 'at':
            at_qq = item.get('data', {}).get('qq')
            break
    message2 = next((item['data']['text'] for item in message1 if item.get('type') == 'text'), None)
    if sender_nickname:
        if message_type == "group":
            print("收到用户：", sender_nickname, "（", user_id, "）在(", group_id, ")发送的消息：", message2)
        else:
            print("收到用户：", sender_nickname, "（", user_id, "）发送的消息：", message2)
    if message2 is None:
        return "_"
    match = re.match(r'([^\d]+)(\d+)', message2)
    parameter = 0
    if match:
        instruction = match.group(1)
        parameter = int(match.group(2))
        if instruction in toolbox:
            toolbox[instruction](user_id, group_id, message_type, parameter, at_qq)
        else:
            chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client, chat_history, save_global_history)
    else:
        if message2 in toolbox:
            toolbox[message2](user_id, group_id, message_type, parameter, at_qq)
        else:
            chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client, chat_history, save_global_history)
    return "_"

if __name__ == '__main__':
    app.run(debug=True, port=5800, host="0.0.0.0")