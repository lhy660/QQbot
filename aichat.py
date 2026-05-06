from flask import Flask, request
import requests
import os
import json
from collections import deque
from openai import OpenAI
from fuctions import toolbox, chat

app = Flask(__name__)

api_key = os.getenv('AIKEY')
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

HISTORY_DIR = "chat_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)
user_histories = {}

def load_user_histories():
    """加载所有用户的历史记录"""
    global user_histories
    if not os.path.exists(HISTORY_DIR):
        return
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith('.json'):
            user_id = filename[:-5]
            filepath = os.path.join(HISTORY_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    user_histories[user_id] = deque(history_data, maxlen=20)
                    print(f"已加载用户 {user_id} 的对话历史，共 {len(history_data)} 条记录")
            except Exception as e:
                print(f"加载用户 {user_id} 的历史记录失败: {e}")

def save_user_history(user_id, history):
    """保存用户历史记录"""
    filepath = os.path.join(HISTORY_DIR, f"{user_id}.json")
    try:
        history_list = list(history)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存用户 {user_id} 的历史记录失败: {e}")

load_user_histories() # 启动时加载历史记录

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
    import re
    match = re.match(r'([^\d]+)(\d+)', message2)
    parameter = 0
    if match:
        instruction = match.group(1)
        parameter = int(match.group(2))
        if instruction in toolbox:
            toolbox[instruction](user_id, group_id, message_type, parameter, at_qq)
        else:
            chat(user_id, group_id, message_type, parameter, at_qq, message2, client, user_histories, save_user_history)
    else:
        if message2 in toolbox:
            toolbox[message2](user_id, group_id, message_type, parameter, at_qq)
        else:
            chat(user_id, group_id, message_type, parameter, at_qq, message2, client, user_histories, save_user_history)
    return "_"

if __name__ == '__main__':
    app.run(debug=True, port=5800, host="0.0.0.0")
