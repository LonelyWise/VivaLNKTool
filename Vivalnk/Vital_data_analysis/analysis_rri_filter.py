#!/usr/bin/env python 
# coding:utf-8

import os
import json
import matplotlib.pyplot as plt
import numpy as np

time_recordTime = 0
rriArray = []
hr_array = []
with open('/Users/xuwei/Desktop/Cardiac-Data/all_completeData.log') as file_to_read:
    while True:
        lines = file_to_read.readline()
        if not lines:
            break
        index = lines.index("{")
        lines = lines[index:len(lines)]
        json_dict = json.loads(lines)

        record_time = json_dict["recordTime"]
        if (time_recordTime == 0):
            time_recordTime = record_time
        else:
            del_time = record_time - time_recordTime
            if del_time > 1000:
                print("时间差值" + str(del_time) + " 当前时间戳" + str(record_time) + " 上一条数据时间戳" + str(time_recordTime))
            time_recordTime = record_time

        hr_vaue = json_dict['hr']
        hr_array.append(hr_vaue)

        rri =json_dict["rri"]
        for rriValue in rri:
            if rriValue != 0:
                rriArray.append(rriValue)



# print(rriArray)

x = np.linspace(1, len(hr_array), len(hr_array), endpoint=True)
plt.plot(x, hr_array)

plt.xlabel("Times")
plt.ylabel("HR")
plt.title("HR Wave")

plt.ylim(10, 300)

plt.legend()  # 显示左下角的图例

plt.show()


x = np.linspace(1, len(rriArray), len(rriArray), endpoint=True)
plt.plot(x, rriArray)

plt.xlabel("Times")
plt.ylabel("RRI")
plt.title("RRI Wave")

plt.ylim(0, 2000)

plt.legend()  # 显示左下角的图例

plt.show()