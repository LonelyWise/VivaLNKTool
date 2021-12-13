#!/usr/bin/env python
# coding:utf-8
'''
将多设备数据日志分离成每个设备一个日志
'''
import json
import os
import re
import time

class MultiDeviceSplicyLog:
    def __init__(self,Splicy_log):
        self.Splicy_log = Splicy_log

    def sord_file_data(self,filepath):
        '''
        :param filepath: 文件夹路径
        :return:
        '''
        datas = []
        list = os.listdir(filepath)
        length = len(list)
        for i in range(0, length):
            path = os.path.join(filepath, list[i])
            self.Splicy_log(path)
            if path.find('DS_Store') > 0:
                continue
            with open(path, 'r') as file_to_read:
                while True:
                    lines = file_to_read.readline()
                    if not lines:
                        break
                    if lines.find('{') >= 0:
                        datas.append(lines)

        return datas


    def data_splicy_print(self,all_data,file_path):
        # 创建文件夹
        dir_name = os.path.join(file_path,'splicy')
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        device_buffer = []
        for lines in all_data:
            splicy_index = lines.index("{")
            json_line = lines[splicy_index:len(lines)]
            json_dict = json.loads(json_line)

            device_name = json_dict['deviceName']
            device_file_path = os.path.join(dir_name,device_name.replace('/', '_') + '.log')

            if device_name not in device_buffer:
                device_buffer.append(device_name)

            fp = open(device_file_path,'a+')
            fp.write(lines)
            fp.close()

        self.Splicy_log(f"Device list:{device_buffer}")

    def splicy_file_log_analysis(self,file_path):
        dir_name = os.path.join(file_path, 'splicy')

        list = os.listdir(dir_name)
        length = len(list)
        for i in range(0, length):
            single_device_data = []
            path = os.path.join(dir_name, list[i])
            self.Splicy_log(path)
            if path.find('DS_Store') > 0:
                continue
            device_name = ''
            with open(path, 'r') as file_to_read:
                while True:
                    lines = file_to_read.readline()
                    if not lines:
                        break
                    if lines.find('{') >= 0:
                        splicy_index = lines.index("{")
                        json_line = lines[splicy_index:len(lines)]
                        json_dict = json.loads(json_line)

                        device_name = json_dict['deviceName']
                        single_device_data.append(json_dict)
            single_device_data.sort(key=lambda f: f["recordTime"])

            self.data_analysis(device_name,single_device_data)

    def data_analysis(self,sn, data_att):
        self.Splicy_log(f'设备号:{sn}分析')
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

                    startLostTime = real_time / 1000
                    startLostTimeLocal = time.localtime(startLostTime)
                    startLostTimeStyle = time.strftime("%Y-%m-%d %H:%M:%S", startLostTimeLocal)
                    self.Splicy_log("数据开始丢失前时间点："+startLostTimeStyle)
                    self.Splicy_log("数据结束丢失时间点："+otherStyleTime)
                    # print(otherStyleTime)
                    self.Splicy_log("数据相差值" + str(del_value))

                real_time = json_dict["recordTime"]

def print_log(msg):
    print(msg)

if __name__ == '__main__':

    file_path = "/Users/weixu/Desktop/test splicy function"
    multi = MultiDeviceSplicyLog(print_log)
    # all_data = multi.sord_file_data(file_path)

    # multi.data_splicy_print(all_data,file_path)
    # multi.data_splicy(all_data,file_path)

    multi.splicy_file_log_analysis()