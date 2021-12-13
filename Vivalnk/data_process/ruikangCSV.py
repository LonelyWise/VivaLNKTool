#!/usr/bin/env python 
# coding:utf-8


import json
import time
import os
import re




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

                if not lines:
                    break
                new_lines = lines.replace('}{','},{')
                new_lines = new_lines.replace('},]','}]')

                json_array = json.loads(new_lines)
                for json_dict in json_array:
                    datas.append(json_dict)


    # datas = sorted(datas, key=lambda x: int(re.search(r'"recordTime":(\d+)', x).group(1)))
    print(len(datas))

    return datas


def data_write_tofile(data_lines, writefilename):
    '''
    :param data_lines: 所有排序后的数据
    :param writefilename: 被写入的文件名
    :return:
    '''
    with open(writefilename, 'a+') as file_to_write:
        for data in data_lines:
            ecg = data['ecg']
            ecg_str = ''
            for ecgValue in ecg:
                ecg_str = ecg_str + ' ' + str(ecgValue)
            file_to_write.write(ecg_str)
            file_to_write.write('\n')

        file_to_write.close()



if __name__ == '__main__':
    file_path = '/Users/xuwei/Downloads/11-张国英'
    write_path = '/Users/xuwei/Downloads/11-张国英/ECGFormat.txt'
    allData = sord_file_data(file_path)
    data_write_tofile(allData,write_path)