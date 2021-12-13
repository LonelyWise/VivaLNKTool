#!/usr/bin/env python 
# coding:utf-8


import itchat
import time
from itchat.content import *
from wxpy import *

def send_frend_msg(self):
    frend_name = ''

    itchat.auto_login(hotReload=True)
    user_name = itchat.search_friends(frend_name)[0]['UserName']
    itchat.send_file('/Users/xuwei/Desktop/')


    bot = Bot()

    my_friends = bot.friends().search('Afina~王小萍', sex=FEMALE, city='杭州')

    friend = ensure_one(my_friends)

    #friend = bot.friends().search('游戏小狗狗', sex=MALE, city='深圳')[0]

    friend.send('这是通过Python发送给你的消息')

gname = '黄大牛工作室'
context = '黄小B是个傻屌'

def SendChatRoomsMsg(gname, context):
    # 获取所有群的相关信息，update=True表示信息更新
    myroom = itchat.get_chatrooms(update=True)
    # myroom = itchat.get_chatrooms()
    # print(room1)
    global username

    # 搜索群名
    myroom = itchat.search_chatrooms(name=gname)
    # print(myroom)
    for room in myroom:
        # print(room)
        if room['NickName'] == gname:
            username = room['UserName']
            itchat.send_msg(context, username)
        else:
            print('No groups found')


# 监听是谁给我发消息
@itchat.msg_register(itchat.content.TEXT)
def text_reply(msg):
    # 打印获取到的信息
    # print(msg)
    itchat.send("您发送了：\'%s\'\n微信目前处于python托管，你的消息我会转发到手机，谢谢" % (msg['Text']), toUserName=msg['FromUserName'])


itchat.auto_login(hotReload=True)
SendChatRoomsMsg(gname, context)
itchat.run()