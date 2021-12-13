#!/usr/bin/env python 
# coding:utf-8

import json
import os
import re
import time

device_name1 = 'B33.00037828'
device_name2 = 'C28.00100006'
device_name3 = 'B33.00033701'
device_name4 = 'B33.00033203'
device_name5 = 'B32.00026059'
device_name6 = 'B32.00025639'

file_path1 = '/Users/xuwei/Desktop/TempWriteFile/37828.log'
file_path2 = '/Users/xuwei/Desktop/TempWriteFile/100006.log'
file_path3 = '/Users/xuwei/Desktop/TempWriteFile/33203.log'
file_path4 = '/Users/xuwei/Desktop/TempWriteFile/32672.log'
file_path5 = '/Users/xuwei/Desktop/TempWriteFile/33701.log'
file_path6 = '/Users/xuwei/Desktop/TempWriteFile/25639.log'

data1 = []
data2 = []
data3 = []
data4 = []
data5 = []
data6 = []

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
    print(sn + '数据分析:')
    firstData = data_att[0]
    lastData = data_att[len(data_att) - 1]

    firstDataTime = firstData['recordTime']/1000
    lastDataTime = lastData['recordTime']/1000

    #理论接收率
    receiveCount = 0
    if sn == device_name2:
        receiveCount = (1587528000 - 1587459600) / 8
    else:
        receiveCount = (1587528000 - 1587459600) / 16
    percent = len(data_att)/receiveCount
    print("接收率为："+ str(percent))


def data_splicy(all_data):

    lines1 = []
    lines2 = []
    lines3 = []
    lines4 = []
    lines5 = []
    lines6 = []
    for lines in all_data:
        index = lines.index("{")
        lines = lines[index:len(lines)]
        json_dict = json.loads(lines)

        recordTime = json_dict['recordTime']
        if recordTime < 1587459600000:
            continue
        if recordTime > 1587528000000:
            continue

        device_id = json_dict['deviceName']

        if device_id == device_name1:
            lines1.append(lines)
            data1.append(json_dict)
        elif device_id == device_name2:
            lines2.append(lines)
            data2.append(json_dict)
        elif device_id == device_name3:
            lines3.append(lines)
            data3.append(json_dict)
        elif device_id == device_name4:
            lines4.append(lines)
            data4.append(json_dict)
        elif device_id == device_name5:
            lines5.append(lines)
            data5.append(json_dict)
        elif device_id == device_name6:
            lines6.append(lines)
            data6.append(json_dict)

    data_write_tofile(lines1, file_path1)
    data_analysis(device_name1, data1)

    data_write_tofile(lines2, file_path2)
    data_analysis(device_name2, data2)

    data_write_tofile(lines3, file_path3)
    data_analysis(device_name3, data3)

    data_write_tofile(lines4, file_path4)
    data_analysis(device_name4, data4)

    data_write_tofile(lines5, file_path5)
    data_analysis(device_name5, data5)

    data_write_tofile(lines6, file_path6)
    data_analysis(device_name6, data6)

if __name__ == '__main__':
    all_data = sord_file_data("/Users/xuwei/Documents/数据分析文档/温度丢失分析/4-22")

    data_splicy(all_data)