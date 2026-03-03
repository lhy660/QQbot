# 基于Flask框架，借助Napcat与Onebot11构建的QQ聊天机器人
onebot11项目地址:
https://github.com/botuniverse/onebot-11/tree/master

napcat项目地址:
https://github.com/NapNeko/NapCatQQ

napcat官方文档:
https://www.napcat.wiki/guide/start-install
### 简介：
这是一个名为“芒果”的智能聊天机器人后端服务。它基于 Python 的 Flask 框架搭建，通过HTTP协议与Napcat客户端通信，为用户在QQ群或私聊中提供AI（使用deepseek模型）对话、签到、转账、银行存取款、抽奖、点赞等一系列趣味互动功能。
### 使用示例：
![示例1](example-image/Image_1757390873674.png)
![示例2](example-image/Image_1757391230418.png)
图一是机器人给用户点名片赞，图二是机器人调用deepseek跟用户聊天。

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
运行qqbot后端程序：
```
python3 aichat.py
```
按ctrl+c退出Flask机器人后端程序。

README.md文档还正在完善，敬请期待……
