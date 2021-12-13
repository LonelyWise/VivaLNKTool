#!/usr/bin/env python 
# coding:utf-8
'''
创建TCP服务端 并接收ECG数据实时绘制
协议是纳龙给的协议
'''

import time
from socket import *
from time import ctime
import matplotlib.pyplot as plt

HOST = '192.168.0.102'
PORT = 9999
BUFSIZ = 1024
ADDR = (HOST, PORT)

tcpSerSock = socket(AF_INET, SOCK_STREAM)   # 创建套接字
tcpSerSock.bind(ADDR)   # 绑定IP和端口
tcpSerSock.listen(5)    # 监听端口，最多5人排队

plt.ion()  # 开启interactive mode 成功的关键函数
plt.figure(1)
t = 1


def analysi_client_data(data):
    print('head' + str(data[0]))

    trID = data[1] << 8 | data[2]
    print('消息序列号' + str(trID))
    bodyLen = data[3] << 8 | data[4]
    print('请求体长度' + str(bodyLen))
    print('保留字节内容' + str(data[5]))
    # body解析
    print('reportId = ' + str(data[6]))
    sequence = data[7] << 8 | data[8];
    print('sequence序列号:' + str(sequence))
    timestamp = data[9] << 24 | data[10] << 16 | data[11] << 8 | data[12]
    print('时间戳:' + str(timestamp) + '   ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)))
    ecg_array = []
    x = []
    j = 0
    # 组装ECG数据
    for i in range(13, 13 + 256):
        j = j + 1
        if j == 2:
            ecg_value = data[i - 1] << 8 | data[i]
            if ecg_value > 32768:
                ecg_value = (65535 - ecg_value + 1) * -1
            x.append(t)
            t = t + 1

            j = 0
            ecg_array.append(ecg_value)

    return x,ecg_array

def bytesToHexString(bs):
    # hex_str = ''
    # for item in bs:
    #     hex_str += str(hex(item))[2:].zfill(2).upper() + " "
    # return hex_str
    return ''.join(['%02X ' % b for b in bs])

texe = bytes([16,17,18,19,20,21,22])
print(bytesToHexString(texe))

while True:
    print('waiting for connection...')
    tcpCliSock, addr = tcpSerSock.accept()    # 建立连接
    print('...connected from:', addr)

    while True:
        data = tcpCliSock.recv(BUFSIZ)
        if not data:
            break

        print('接收到客户端的数据:')
        if data[0] == 0x9d:
            print(data)
            x,ecg_array = analysi_client_data(data)
            print(ecg_array)
            # plt.clf()
            plt.plot(x, ecg_array, '-r')
            plt.pause(0.01)
            # 回复客户端的内容
            sendByte = bytes([data[6], data[7], data[8]])
            tcpCliSock.send(sendByte)
        else:
            content = '[%s] %s' % (bytes(ctime(), "utf-8"), data)
            print(content)
            print(str(data,encoding='utf-8'))
            backContent = 'OK'
            tcpCliSock.send(backContent.encode("utf-8"))
    tcpCliSock.close()

tcpSerSock.close()


