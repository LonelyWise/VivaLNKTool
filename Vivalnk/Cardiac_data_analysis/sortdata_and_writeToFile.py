#!/usr/bin/env python 
# coding:utf-8
# 排序专用 310和330都适用
import json
import os
import re
import time
from draw_cardiac_data import DrawWave


rriArray = []
hr_array = []
ecg_array = []
rwl_array = []
rwlcount = 0
rwl_count = 0
time_array = []

def sord_file_data(filepath):
    '''
    :param filepath: 文件夹路径
    :return:
    '''
    datas = []
    list = os.listdir(filepath)
    length = len(list)
    for i in range(0, length):
        path = os.path.join(filepath, list[i])
        print(path)
        with open(path, 'r') as file_to_read:
            while True:
                lines = file_to_read.readline()
                # print(lines)
                if not lines:
                    break
                if lines.find('{') >= 0:
                    # index = lines.index("{")
                    # lines = lines[index:len(lines)]
                    datas.append(lines)

    datas = sorted(datas, key=lambda x: int(re.search(r'"recordTime":(\d+)', x).group(1)))
    # print(datas)

    return datas

def data_write_tofile(data_lines, writefilename):
    '''
    :param data_lines: 所有排序后的数据
    :param writefilename: 被写入的文件名
    :return:
    '''
    with open(writefilename, 'a+') as file_to_write:
        for data in data_lines:
            file_to_write.write(data)

        file_to_write.close()


def data_lost_analysis(filePath):
    real_time = 0
    with open(filePath) as file_to_read:
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

            if real_time == 0:
                real_time = json_dict["recordTime"]
            else:
                del_value = json_dict["recordTime"] - real_time
                real_time = json_dict["recordTime"]

                if del_value > 1050:
                    timeStamp = json_dict["recordTime"] / 1000
                    timeArray = time.localtime(timeStamp)
                    otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)
                    print("数据相差值" + str(del_value))
                    print(otherStyleTime)

            hr_vaue = json_dict['hr']
            hr_array.append(hr_vaue)

            rri = json_dict["rri"]
            for rriValue in rri:
                if rriValue != 0:
                    rriArray.append(rriValue)

            ecg_arr = json_dict["ecg"]
            for ecgValue in ecg_arr:
                ecg_array.append(ecgValue / 1000.0)

            global rwl_count
            global  rwlcount
            rwl_arr = json_dict["rwl"]
            for i in range(0, len(rwl_arr)):
                if rwl_arr[i] != -1:
                    rwlcount += 1
                    rwl_value = rwl_arr[i] + rwl_count * 128
                    rwl_array.append(rwl_value)
            rwl_count += 1



if __name__ == '__main__':
    # 排序文件夹下所有文件的所有数据
    # filepath = './data'
    # sort_data = sord_file_data(filepath)
    # 将数据写入一个文件中
    # write_file = filepath + '/all_completeData.log'
    # data_write_tofile(sort_data, write_file)
    # 分析数据丢失
    data_lost_analysis("/Users/xuwei/Desktop/VVRealDataLog 2020-06-17 18-15.log")
    # 画图
    drawWave = DrawWave()

    drawWave.draw_hr(hr_array)

    drawWave.draw_ecg(ecg_array,rwl_array,time_array)