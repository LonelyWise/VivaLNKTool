#!/usr/bin/env python 
# coding:utf-8
import os
import re
import numpy
from draw_cardiac_data import DrawWave

filename = 'data/Data 2019-07-11 14-37.log'
writefilename = './data/write_test.txt'

x_array = []
y_array = []
z_array = []
ecg_array = []
ecg_number = 0
rwl_array = []
rwl_count = 0
ecg_hz = 128
recordtime = 0
rricount = 0
rwlcount = 0
record_rri_line = ''
hr_array = []

def writeDataToFile(data):
    with open(writefilename, 'a+') as file_to_write:
        file_to_write.write(data)

        file_to_write.close()

# 排序数据
def sort_cardiac_data(file_lines):
    time_sort_list = []
    for group_arry in file_lines:
        first_line = group_arry[0]
        time_value = re.findall(r'dateTime=(.+?),', first_line)
        time_sort_list.append(int(time_value))
    # 获取下标
    indices = numpy.argsort(time_sort_list)

    for index in indices:
        after_sort_line = file_lines[index]


with open(filename,'r') as file_to_read:
    while True:
        lines = file_to_read.readline()
        if not lines:
            break
        if lines.find("dateTime=") >= 0:
            index = lines.index("{")
            recordtime = lines[index + 10:index + 10 + 13]
        # RRI
        if lines.startswith('Troy_RRI'):
            record_rri_line = lines
            rri_line = lines.strip('Troy_RRI:')
            rri_line = rri_line.strip('\n')
            rri_array = rri_line.split(',')
            for rri_value in rri_array:
                if int(rri_value) != 0:
                    rricount += 1
        # 心率值
        if lines.startswith('Troy_HR:'):
            hr_line = lines.strip('Troy_HR:')
            hr_line = hr_line.strip('\n')
            hr = int(hr_line)
            hr_array.append(hr)
        # 分解acc数据
        if lines.startswith('XYZ:'):
            acc_line = lines.strip('XYZ:')
            acc_arr_group = acc_line.split(',')
            for i in range(0, len(acc_arr_group)):
                acc_every = acc_arr_group[i].split(' ')
                xValue = int(acc_every[0])
                yValue = int(acc_every[1])
                zValue = int(acc_every[2])
                x_array.append(xValue)
                y_array.append(yValue)
                z_array.append(zValue)
        if lines.startswith('RWL:'):
            rwl_line = lines.strip('RWL:')
            rwl_line = rwl_line.strip('\n')
            rwl_arr = rwl_line.split(',')
            rwl_arr = list(map(int, rwl_arr))

            for i in range(0, len(rwl_arr)):
                if rwl_arr[i] != 255:
                    rwlcount += 1
                    rwl_value = rwl_arr[i] + rwl_count * ecg_hz
                    rwl_array.append(rwl_value)
            rwl_count += 1
            # 判断不匹配的数据
            if rricount != rwlcount:
                rricount = 0
                rwlcount = 0
                dataStr = '不匹配\n' + lines + record_rri_line + str(recordtime) + '\n'
                writeDataToFile(dataStr)


        # 组装ECG数据
        if lines.startswith('ECG:'):
            ecg_number += 1
            ecg_line = lines.strip('ECG:')
            ecg_line = ecg_line.strip('\n')
            ecg_arr = ecg_line.split(',')
            print(len(ecg_arr))
            ecg_array = ecg_array + ecg_arr

if __name__ == '__main__':
    drawWave = DrawWave()

    # 画HR分布图
    drawWave.draw_hr(hr_array)
    # 画acc图形
    drawWave.draw_acc(x_array, y_array, z_array)
    # 画ecg图形
    # 将数组中的数据转成float型
    # ecg_array = list(map(float, ecg_array))
    if len(ecg_array) != 0:
        ecg_value_array = []
        for ecgValue in ecg_array:
            ecg_value_array.append(float(ecgValue))
        drawWave.draw_ecg(ecg_value_array, rwl_array)



