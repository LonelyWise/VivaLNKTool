#!/usr/bin/env python
# coding:utf-8

import json
import requests
import os
import threading
import time
import datetime
'''
使用最原始的60S下载接口
此文件会使用多线程下载数据
目前已被废弃
'''
Token = ''

every_hour_data = []

class DownloadDataFromVCloud:

    def __init__(self,write_path,app_id,Universal_log):
        self.write_path = write_path
        self.app_id = app_id
        self.Universal_log = Universal_log

    def input_download_param(self,sn,total_start,total_end):
        '''
        返回下载时间段的所有数据
        :param sn:
        :param total_start:
        :param total_end:
        :return:
        '''
        every_hour_data = []
        hour_time_slice = self.cut_time_slice(total_start,total_end,3600)

        print(hour_time_slice)
        all_data = []
        for i in hour_time_slice:
            data_part = self.start_multi_thread(sn, i[0], i[1])
            if data_part is not None:
                all_data += data_part

        if len(all_data) == 0:
            log_str = "no data is downloaded"
            self.Universal_log(log_str)
            return []
        all_data.sort(key=lambda f: f["recordTime"])

        return all_data

    def start_multi_thread(self,sn,start, end):
        start_str = datetime.datetime.fromtimestamp(start / 1000).strftime('%Y-%m-%d %H:%M:%S')
        end_str = datetime.datetime.fromtimestamp(end / 1000).strftime('%Y-%m-%d %H:%M:%S')
        self.Universal_log('此轮下载的开始时间:'+start_str+'  结束时间'+end_str)

        min_start = time.time()
        threads = []
        minute_time_slice = self.cut_time_slice(start,end,60)
        for i in range(len(minute_time_slice)):
            slice_start = minute_time_slice[i]
            thread = UniversalThread(i, 'thread-1'+str(i),sn,slice_start[0],slice_start[1],self.app_id)
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
        global every_hour_data
        self.Universal_log(f"此轮的数据条数= {len(every_hour_data)}")
        universal_hour_data = every_hour_data
        every_hour_data = []
        universal_hour_data.sort(key=lambda f: f["recordTime"])

        if self.write_path != '':
            snId = sn.replace(".", "%2F")
            file_name = os.path.join(self.write_path, f"{snId}_{start}_{end}.log")
            self.Universal_log('数据写入的文件名：'+file_name)
            if os.path.exists(file_name):
                self.Universal_log(f"{file_name} exists, skip writing")
                with open(file_name) as input:
                    return json.load(input)

            with open(file_name, "a+") as output:
                for line_dict in universal_hour_data:
                    json.dump(line_dict, output)
                    output.write('\n')
                output.close()

        diff_time = time.time()-min_start
        self.Universal_log(f'耗时{int(diff_time)}S  ,继续下一轮')
        return universal_hour_data


    def download_data_from_vcloud(self,sn, dl_start, dl_end):
        type = "TemperatureRaw"
        if sn.find('O2') >= 0:
            type = "SpO2Raw"

        query_param_dict = {
            "sensorid": sn,
            "appId": self.app_id,
            'type': type,
            "start": dl_start,
            "end": dl_end,
        }
        base_url = "https://zciwpugh35.execute-api.ap-south-1.amazonaws.com/test/eventList"

        try:
            response = requests.get(base_url, params=query_param_dict)
        except Exception as e:
            print(e)

        json_dict = json.loads(response.content)
        json_data = json_dict["data"]
        if len(json_data) == 0:
            return None
        return json_data

    def cut_time_slice(self,start, end,time):
        time_slice = []
        it = start
        while it < end:
            new_end = it + time * 1000 - 1
            if end <= new_end:
                time_slice.append((it, end))
                break
            else:
                time_slice.append((it, new_end))
                it = new_end + 1
        return time_slice



class UniversalThread (threading.Thread):
    def __init__(self, threadID, name,sn,start_time,end_time,appid):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.sn = sn
        self.appid = appid


    def run(self):
        self.dl_UniversalData_from_vCloud_thread(self.sn,self.start_time,self.end_time)

    def dl_UniversalData_from_vCloud_thread(self,sn, dl_start, dl_end):
        type = "TemperatureRaw"
        if sn.find('O2') >= 0:
            type = "SpO2Raw"
        elif sn.find('004D32') > 0:
            type = "BPRaw"

        query_param_dict = {
            "sensorid": sn,
            "appId": self.appid,
            'type': type,
            "start": dl_start,
            "end": dl_end,
        }
        base_url = "https://zciwpugh35.execute-api.ap-south-1.amazonaws.com/test/eventList"
        try:
            response = requests.get(base_url, params=query_param_dict)
            json_dict = json.loads(response.content)
            json_data = json_dict["data"]
            if len(json_data) == 0:
                return
            print('start:' + str(dl_start) + '  ' + 'end:' + str(dl_end))
            print(len(json_data))
            for data_dict in json_data:
                record_time = data_dict['recordTime']
                ecg_json = data_dict['data']
                ecg_json['recordTime'] = record_time
                ecg_json['receiveTime'] = data_dict['receiveTime']
                every_hour_data.append(ecg_json)
        except Exception as e:
            print(e)


