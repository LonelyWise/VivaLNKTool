#!/usr/bin/env python 
# coding:utf-8
import os
import matplotlib.pyplot as plt
import numpy as np
import re
import time, datetime

fig = plt.figure()
def call_back(event):
    axtemp=event.inaxes
    x_min, x_max = axtemp.get_xlim()
    fanwei = (x_max - x_min) / 10
    if event.button == 'up':
        axtemp.set(xlim=(x_min + fanwei, x_max - fanwei))
        print('up')
    elif event.button == 'down':
        axtemp.set(xlim=(x_min - fanwei, x_max + fanwei))
        print('down')
    fig.canvas.draw_idle()  # 绘图动作实时反映在图像上
fig.canvas.mpl_connect('scroll_event', call_back)
fig.canvas.mpl_connect('button_press_event', call_back)


def caculate_sleep():
    record_start = 0
    record_sleep_time = 0
    with open('./data/fb_x.txt', 'r') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break
            if record_sleep_time == 0:
                if lines.startswith("{dateTime="):
                    start_time = re.findall(r"{dateTime=(.+?),",lines)
                    record_sleep_time = int(start_time[0])

            if lines.startswith('HR:'):
                sleep_start = re.findall(r"SS:(.+?),",lines)
                if int(sleep_start[0]) != 0:
                    # print('start:' + sleep_start[0])
                    record_start = int(sleep_start[0])
                sleep_end = re.findall(r"SE:(.+?),",lines)
                if int(sleep_end[0]) != 0:
                    # 计算出开始睡眠的时间点
                    record_sleep_time = record_sleep_time/1000 + record_start*60
                    timeArray = time.localtime(record_sleep_time)
                    otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
                    print("开始睡觉的时间：" + otherStyleTime)
                    # 统计睡眠的分钟数
                    difference = int(sleep_end[0]) - record_start
                    print('睡眠时长:' + str(difference) + '分钟')
                    # 计算结束睡眠的时间点
                    record_sleep_time = record_sleep_time + difference*60
                    endTimeArray = time.localtime(record_sleep_time)
                    endSleepTime = time.strftime("%Y--%m--%d %H:%M:%S", endTimeArray)
                    print('睡眠结束时间:' + endSleepTime)
                    # 计算出睡眠后初始化
                    record_start = 0
                    record_sleep_time = 0
def draw_rsi():
    array = []
    with open('./data/10810_x.txt', 'r') as file_to_read:
        while True:
            lines = file_to_read.readline()
            # print (lines)
            if not lines:
                break
            if lines.startswith('HR:'):
                arr = lines.split('RSI=')
                index = arr[1]
                arrat = index.split(',')
                inde11 = arrat[0]
                con = int(inde11)
                if con:
                    array = array + [con]
                # print(array)

    x = np.linspace(1, len(array), len(array), endpoint=True)
    plt.bar(x, array)

    plt.xlabel("Time(s)")
    plt.ylabel("RSI")
    plt.title("FB RSI Distribution")

    plt.ylim(-100, 100)

    plt.legend()  # 显示左下角的图例

    plt.show()




if __name__ == '__main__':
    # 计算睡眠时间
    caculate_sleep()
    # # 画RSI分布图
    draw_rsi()

