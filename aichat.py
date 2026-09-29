from flask import Flask, request # type: ignore
import requests
import os
import json
import re
from openai import OpenAI # type: ignore
from fuctions import toolbox, chat

app = Flask(__name__)

# 初始化 OpenAI 客户端
api_key = os.getenv('AIKEY')
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


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
            chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client)
    else:
        if message2 in toolbox:
            toolbox[message2](user_id, group_id, message_type, parameter, at_qq)
        else:
            chat(user_id, group_id, message_type, parameter, at_qq, message2, sender_nickname, client)
    return "_"

if __name__ == '__main__':
    app.run(debug=True, port=5800, host="0.0.0.0")