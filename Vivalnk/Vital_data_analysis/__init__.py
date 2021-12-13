#!/usr/bin/env python 
# coding:utf-8

import re
import time, datetime
import json
import numpy
from draw_vital_wave import DrawVitalWave

filename = 'data/xiaofei_fb.txt'

record_sleep_time = 0
record_start = 0
rsi_array = []


def analysis_sleep(lines):
    global record_sleep_time
    global record_start
    if record_sleep_time == 0:
        if lines.startswith("{dateTime="):
            start_time = re.findall(r"{dateTime=(.+?),", lines)
            record_sleep_time = int(start_time[0])
    if lines.startswith('HR:'):
        sleep_start = re.findall(r"SS:(.+?),", lines)
        if int(sleep_start[0]) != 0:
            # print('start:' + sleep_start[0])
            record_start = int(sleep_start[0])
        sleep_end = re.findall(r"SE:(.+?),", lines)
        sleep_end_can = re.findall(r"SEC:(.+?) ", lines)
        sleep_end = sleep_end_can
        if int(sleep_end[0]) != 0:
            # print('end' + sleep_end[0])
            # 计算出开始睡眠的时间点
            record_sleep_time = record_sleep_time / 1000 + record_start * 60
            timeArray = time.localtime(record_sleep_time)
            otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
            print("开始睡觉的时间：" + otherStyleTime)
            # 统计睡眠的分钟数
            difference = int(sleep_end[0]) - record_start
            print('睡眠时长:' + str(difference) + '分钟')
            # 计算结束睡眠的时间点
            record_sleep_time = record_sleep_time + difference * 60
            endTimeArray = time.localtime(record_sleep_time)
            endSleepTime = time.strftime("%Y--%m--%d %H:%M:%S", endTimeArray)
            print('睡眠结束时间:' + endSleepTime)
            # 计算出睡眠后初始化
            record_start = 0
            record_sleep_time = 0

        rsi_str = re.findall(r"RSI=(.+?),", lines)
        rsi_value = int(rsi_str[0])
        rsi_array.append(rsi_value)

x_array = []
y_array = []
z_array = []
def analysis_acc(lines):
    acc_line = re.findall(r"acc='(.+?)',", lines)
    acc_string = acc_line[0]

    acc_string = acc_string.replace('[', '')
    acc_string = acc_string.replace(']', '')

    acc_arr = acc_string.split(',')

    for i in range(1,len(acc_arr)+1):
        if i % 3 == 0:
            xValue = int(acc_arr[i-3])
            yValue = int(acc_arr[i-2])
            zValue = int(acc_arr[i-1])
            x_array.append(xValue)
            y_array.append(yValue)
            z_array.append(zValue)


with open(filename,'r') as file_to_read:
    while True:
        lines = file_to_read.readline()
        if not lines:
            break
        analysis_sleep(lines)
        # analysis_acc(lines)

# 画安卓手机json数据
# with open('./data/logs_12.txt','r') as file_to_read:
#     while True:
#         lines = file_to_read.readline()
#         if not lines:
#             break
#         data = json.loads(lines)
#         acc = data['data']['acc']
#         for accValue in acc:
#             x = accValue['x']
#             y = accValue['y']
#             z = accValue['z']
#             x_array.append(x)
#             y_array.append(y)
#             z_array.append(z)
# 数据排序(只使用安卓导出来的数据)
def sort_by_record_time(file_path):
    reader = open(file_path, "r")
    lines = []
    record_time_mills_list = []
    for line in reader:

        data = json.loads(line)
        begin_index = data['data']["time"]
        print(begin_index)

        lines.append(line)
        record_time_mills_list.append(begin_index)
    print(record_time_mills_list)
    # 获取时间排序的下标
    indices = numpy.argsort(record_time_mills_list)
    print(indices)
    writer = open(file_path, "w")
    for index in indices:
        writer.write(lines[index])
    writer.close()

if __name__ == '__main__':
    draw_wave = DrawVitalWave()
    # draw_wave.draw_acc(x_array,y_array,z_array)
    #
    #
    # sort_by_record_time('./data/data.txt')