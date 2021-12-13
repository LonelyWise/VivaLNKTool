#!/usr/bin/env python 
# coding:utf-8
import os
import json
import time
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as mp
import matplotlib.dates as mdate
import matplotlib.ticker as mtick
# import pandas as pd

time_recordTime = 0
rriArray = []
hr_array = []
ecg_array = []
rwl_array = []
rwlcount = 0
rwl_count = 0
time_array = []

last_rwl_value = 0

with open('data/Data 2019-07-11 14-37.log') as file_to_read:
    while True:
        lines = file_to_read.readline()
        if not lines:
            break
        index = lines.index("{")
        lines = lines[index:len(lines)]
        json_dict = json.loads(lines)

        timeStamp = json_dict["recordTime"]
        timeArray = time.localtime(timeStamp)
        otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
        time_array.append(otherStyleTime)

        hr_vaue = json_dict['hr']
        hr_array.append(hr_vaue)

        rri = json_dict["rri"]
        for rriValue in rri:
            if rriValue != 0:
                rriArray.append(rriValue)

        ecg_arr = json_dict["ecg"]
        for ecgValue in ecg_arr:
            ecg_array.append(ecgValue / 1000.0)

        rwl_arr = json_dict["rwl"]
        for i in range(0, len(rwl_arr)):
            if rwl_arr[i] != -1:
                rwlcount += 1
                rwl_value = rwl_arr[i] + rwl_count * 128
                rwl_array.append(rwl_value)
        rwl_count += 1

# print(rwl_array)
# print(ecg_array)
x_lenth = len(ecg_array) / 128
print(x_lenth)
pltecg = plt.subplot(2, 1, 1)
plt.sca(pltecg)
x = np.linspace(0, x_lenth, len(ecg_array), endpoint=True)
x_array = []
x_count = 1
for j in time_array:
    x_array.append(x_count);
    x_count += 1
plt.plot(x, ecg_array)
plt.xticks(x_array,time_array)
for i in range(0, len(rwl_array) - 1):
    x0 = rwl_array[i]
    y0 = ecg_array[x0]
    x0 = x0 / 128
    plt.scatter(x0, y0, s=20, color='r', marker='*')  # 散点图
plt.xlabel("Times")
plt.ylabel("ECG")
plt.title("ECG Wave")
plt.ylim(-4, 4)
# plt.legend()  # 显示左下角的图例

plthr = plt.subplot(2, 1, 2)
plt.sca(plthr)
hr = np.linspace(0, len(hr_array), len(hr_array), endpoint=True)
plt.plot(hr, hr_array)
plt.xlabel("Times")
plt.ylabel("HR")
plt.title("HR Wave")
plt.ylim(0, 200)

plt.show()



