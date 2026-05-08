# 基于Flask框架，借助Napcat与Onebot11构建的QQ聊天机器人
onebot11项目地址:
https://github.com/botuniverse/onebot-11/tree/master

napcat项目地址:
https://github.com/NapNeko/NapCatQQ

napcat官方文档:
https://www.napcat.wiki/guide/start-install

### 简介：
这是一个名为“芒果”的智能聊天机器人后端服务。它基于 Python 的 Flask 框架搭建，通过HTTP协议与Napcat客户端通信，为用户在QQ群或私聊中提供AI（使用deepseek模型）对话、签到、转账、银行存取款、抽奖、点赞等一系列趣味互动功能。
### 最近更新：
1.代码结构优化：将主程序（aichat.py）与固定交互功能（functions.py）分离，提升代码可读性与维护性。

2.对话机制升级：聊天模式由“一对一私聊”调整为“群聊环境下的点对点交互”，并将底层模型切换为 DeepSeek-V4-Pro，增强响应质量与上下文处理能力。

3.智能调用功能：借助 DeepSeek 的 Tool Calls 机制，芒果能根据语义自动判断并调用对应功能。即使你不使用标准关键词，它也能理解你的意图，准确调用对应功能（目前已支持“抽金币”、“给我点赞”、“菜单”、”账户“、”签到“五个功能）。

### 使用示例：
![示例1](example-image/1.png)
![示例2](example-image/2.png)
![示例2](example-image/3.png)
图一是机器人给用户点名片赞，图二是机器人调用deepseek跟用户聊天，图三是机器人智能调用固定交互功能。

## 注意⚠️
需要deepseek的api才能使用，在使用前请确保拥有key。

## 必看⚠️
HTTP服务端(即收信息端）端口为：
```
5700
```
HTTP客户端（即发信息端）端口为：
```
5800
```
当然你可以在aichat.py文件中自行修改

⚠️请将fuctions.py的第10行中的qq号更改为自己qq机器人的qq号。

# 部署
请使用Debian/Ubuntu系统部署，推荐Debian12+，Ubuntu22.04+
安装依赖：
```
sudo apt update && sudo apt install git python3 python3-venv python3-pip
```
克隆本项目：
```
git clone --depth=1 https://github.com/lhy660/QQbot.git
```
进入项目目录：
```
cd QQbot
```
创建python虚拟环境：
```
python3 -m venv qqbot
```
登入虚拟环境：
```
source qqbot/bin/activate
```
安装所需要库：
```
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple 
```
设置deepseek api的key：
```
export AIKEY={输入你的ket}
```
运行qqbot后端程序：
```
python3 aichat.py
```
按ctrl+c退出Flask机器人后端程序。

README.md文档还正在完善，敬请期待……
