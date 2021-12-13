#!/usr/bin/env python
# coding:utf-8
'''
测试HR算法数据（之前已经采集好的数据）
'''

import time
import datetime
import os
import json
import matplotlib.pyplot as plt
import numpy as np
import Test_tool.TestDB as testDB

def assemble_ecg_file():
    '''
    将之前采集csv的ECG数据处理为json格式并存储
    :return:
    '''
    list = os.listdir('/Users/xw/ProjectCode/维灵科技/Original-QRS/algorithms/data/hrdb')
    length = len(list)
    for i in range(0, length):
        file = list[i]
        if file.find('ECG') > 0:
            path = os.path.join('/Users/xw/ProjectCode/维灵科技/Original-QRS/algorithms/data/hrdb', list[i])
            print(path)

            json_array = []
            with open(path) as file_to_read:
                while True:
                    lines = file_to_read.readline()
                    if not lines:
                        break

                    array = lines.split(',')
                    print(array)
                    timeStr = array[0] + ' ' + array[1]
                    print(timeStr)
                    index = timeStr.index(".")
                    timeStr1 = timeStr[0:index]

                    print(timeStr1)
                    start_time_value = int(
                        time.mktime(datetime.datetime.strptime(timeStr1, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000
                    print(start_time_value)
                    ecg = []
                    for i in range(2, len(array)):
                        ecg_str = array[i]
                        if i == 129:
                            ecg_str = ecg_str.replace('\n', '')
                        ecg_value = int(ecg_str)
                        ecg.append(ecg_value)
                    dict = {}
                    dict['ecg'] = ecg
                    dict['recordTime'] = start_time_value
                    dict['deviceName'] = 'ECGRec_202003/C600001'
                    json_array.append(dict)

            file_name = os.path.join('/Users/xw/Desktop/HRCSV', f"{file}.log")
            print(file_name)

            with open(file_name, "w") as output:
                json.dump(json_array, output)
                output.close()

def process_simulation_data():

    file_path = '/Users/xuwei/Desktop/TestDataAlgo'
    list = os.listdir(file_path)
    length = len(list)
    for i in range(0, length):
        file = list[i]
        path = os.path.join(file_path, list[i])
        print(path)

        json_array = []
        with open(path) as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break
                index = lines.index("{")
                lines = lines[index:len(lines)]
                json_dict = json.loads(lines)
                json_array.append(json_dict)

        file = file.replace('.log','')
        file_name = os.path.join(file_path, f"{file}.txt")
        print(file_name)

        with open(file_name, "w") as output:
            json.dump(json_array, output)
            output.close()


def draw_ecg_wave():
    '''
    绘制hrdb中ecg的心电图
    :return:
    '''
    ecg = []
    with open('./hrdb/002_ECG.csv') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break

            array = lines.split(',')
            # print(array)
            timeStr = array[0] + ' ' + array[1]
            # print(timeStr)
            index = timeStr.index(".")
            timeStr1 = timeStr[0:index]

            # print(timeStr1)
            start_time_value = int(
                time.mktime(datetime.datetime.strptime(timeStr1, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000
            # print(start_time_value)

            for i in range(2, len(array)):
                ecg_str = array[i]
                if i == 129:
                    ecg_str = ecg_str.replace('\n', '')
                ecg_value = int(ecg_str)
                ecg.append(ecg_value)
            # print(ecg)

    plt.plot(ecg)
    plt.ylim(-5000, 5000)

    plt.legend()  # 显示左下角的图例
    plt.show()

def draw_polor_and_ecgpatch():
    '''
    绘制对比图形并存储
    :return:
    '''


    for n in range(1,44):
        common_name= ''
        if n < 10:
            common_name = '00'+str(n)
        else:
            common_name = '0' + str(n)

        polor_hr = []
        polar_name = '_Polar.csv'
        polar_path = './hrdb/'
        polar_complete_path = polar_path+common_name+polar_name
        with open(polar_complete_path) as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break
                array = lines.split(',')
                hr_value = int(array[2])
                polor_hr.append(hr_value)
        print(len(polor_hr))

        ecg_hr = []
        ecg_name = '_ECG.log'
        ecg_path = './ECG-HR(1.0.7结果)/'
        ecg_complete_path = ecg_path + common_name + ecg_name
        with open(ecg_complete_path) as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break
                array = lines.split(',')
                array.pop()
                for i in range(0,len(array)):
                    hr_value = int(array[i])
                    ecg_hr.append(hr_value)
        print(len(ecg_hr))


        qrs_hr = []
        qrs_name = '_QRS.log'
        qrs_path = './QRS(1.9.0)/'
        qrs_complete_path = qrs_path + common_name + qrs_name
        with open(qrs_complete_path) as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break
                json_array = json.loads(lines)
                for json_dict in json_array:
                    hr_value = json_dict['hr']
                    qrs_hr.append(hr_value)

        print(len(qrs_hr))

        polar_x = np.linspace(0, 1, len(polor_hr))
        ecg_x = np.linspace(0, 1, len(ecg_hr))
        qrs_x = np.linspace(0, 1, len(qrs_hr))
        polar_label = 'polar' + '\n' + 'HR Count='+str(len(polor_hr))
        plt.plot(polar_x,polor_hr, label=polar_label)
        vivalnk_label = 'VivaLNK(1.0.7)' + '\n' + 'HR Count=' + str(len(ecg_hr))
        plt.plot(ecg_x,ecg_hr,label=vivalnk_label)
        vivalnk_label = 'VivaLNK(1.0.9)' + '\n' + 'HR Count=' + str(len(qrs_hr))
        plt.plot(qrs_x, qrs_hr, label=vivalnk_label)
        plt.ylim(-5, 250)

        save_path = '/Users/xuwei/Desktop/QRS算法验证/QRS(1.0.9)/' + common_name + '.png'
        plt.legend(loc=0)  # 显示左下角的图例
        plt.savefig(save_path)
        plt.show()



if __name__ == "__main__":
    # 数据处理出
    # assemble_ecg_file()
    # 绘制图形
    draw_polor_and_ecgpatch()

    # draw_ecg_wave()

    # process_simulation_data()






