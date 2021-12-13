#!/usr/bin/env python
# coding:utf-8

import json
import os
import re
import time

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

def data_analysis(sn,data_att):
    print(sn+'数据分析:')
    real_time = 0
    for json_dict in data_att:
        if real_time == 0:
            real_time = json_dict["recordTime"]
        else:
            del_value = json_dict["recordTime"] - real_time


            if del_value > 1050:
                timeStamp = json_dict["recordTime"] / 1000

                timeArray = time.localtime(timeStamp)
                otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", timeArray)

                startLostTime = real_time/1000
                startLostTimeLocal = time.localtime(startLostTime)
                startLostTimeStyle = time.strftime("%Y--%m--%d %H:%M:%S", startLostTimeLocal)
                print("数据开始丢失前时间点：")
                print(startLostTimeStyle)
                print(real_time)
                print("数据结束丢失时间点：")
                print(otherStyleTime)
                print(timeStamp)
                print("数据相差值" + str(del_value))

            real_time = json_dict["recordTime"]
def data_splicy(all_data,file_path):

    deviceId_buffer = []
    for lines in all_data:
        index = lines.index("{")
        lines = lines[index:len(lines)]
        json_dict = json.loads(lines)

        device_id = json_dict['deviceId']
        if device_id not in deviceId_buffer:
            deviceId_buffer.append(device_id)

    all_data_buffer = []
    all_line_buffer = []
    for deviceName in deviceId_buffer:
        alone_device_lines = []
        alone_device_data = []
        for lines in all_data:
            index = lines.index("{")
            lines = lines[index:len(lines)]
            json_dict = json.loads(lines)

            device_id = json_dict['deviceId']
            if deviceName == device_id:
                alone_device_lines.append(lines)
                alone_device_data.append(json_dict)

        all_line_buffer.append(alone_device_lines)
        all_data_buffer.append(alone_device_data)


    for i in range(len(deviceId_buffer)):
        device_name = deviceId_buffer[i]
        alone_device_path = file_path +'/' + device_name.replace('/','_') + '.log'
        data_write_tofile(all_line_buffer[i], alone_device_path)
        data_analysis(device_name, all_data_buffer[i])


if __name__ == '__main__':

    file_path = '/Users/xuwei/Desktop/renbinqi'
    all_data = sord_file_data(file_path)

    data_splicy(all_data,file_path)
