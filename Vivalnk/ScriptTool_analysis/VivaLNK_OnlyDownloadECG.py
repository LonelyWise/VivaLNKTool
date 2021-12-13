#!/usr/bin/env python 
# coding:utf-8
import time
import datetime
import requests
import json
import os
import threading
'''
最早的下载接口，仅支持ECG下载
不需要使用secret秘钥
'''

MAX_DURATION = 1000 * 3600  # 1 hour
every_hour_data = []
download_error = []
class download_ecg_data:

    def __init__(self,write_path,app_id,Print_log):
        self.write_path = write_path
        self.app_id = app_id
        self.Print_log = Print_log
        self.Print_log('开始下载ECG数据')
    def download(self, sn, start, end):
        time_slice = []
        it = start
        while it < end:
            new_end = it + MAX_DURATION - 1
            if end <= new_end:
                time_slice.append((it, end))
                break
            else:
                time_slice.append((it, new_end))
                it = new_end + 1
        all_data = []
        if sn.find('ECGRec_') >= 0:
            threads_array = []
            for i in time_slice:
                # ecg_thread = ECGThread(i, 'thread-1'+str(i),sn,i[0],i[1])
                # ecg_thread.start()
                # threads_array.append(ecg_thread)

            # for t in threads_array:
            #     t.join()

            # global every_hour_data
            # all_data = every_hour_data
                start_str = datetime.datetime.fromtimestamp(i[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(i[1] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.Print_log('此轮下载的开始时间:' + start_str + '  结束时间' + end_str)
                # 从javaAPI下载
                data_part = self.download_single(sn, i[0], i[1])
                if data_part is not None:
                    all_data += data_part
        else:
            for i in time_slice:
                # 从vCloud直接下载
                data_part = self.start_multi_thread(sn, i[0], i[1])
                if data_part is not None:
                    all_data += data_part

        # 判断失败的次数继续下载
        fail_count = 1
        fail_threads_array = []
        global download_error
        fail_download_array = download_error
        download_error = []
        if len(fail_download_array) != 0:
            self.Print_log(f'下载失败的条数:{len(fail_download_array)}')
            for fail_dict in fail_download_array:
                fail_st = fail_dict['st']
                fail_et = fail_dict['et']
                fail_thread_name = fail_dict['threadName']
                thread = myThread(fail_count, fail_thread_name , sn, fail_st, fail_et, self.app_id)
                thread.start()

                fail_threads_array.append(thread)

            for t in fail_threads_array:
                t.join()

        if len(all_data) == 0:
            self.Print_log("no data is downloaded")
            return

        all_data.sort(key=lambda f: f["recordTime"])

        missing_tick = []
        if True:
            missing = int((end - start) / 1000 - len(all_data))
            self.Print_log(f"totally {missing} seconds missing")
            for i in range(len(all_data) - 1):
                end_tick = all_data[i + 1]["recordTime"]
                start_tick = all_data[i]["recordTime"]
                delta = end_tick - start_tick
                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')

                if abs(delta) < 500:
                    self.Print_log(f"duplicated from {start_str} to {end_str}")

                if delta > 1100:
                    self.Print_log(f"part one: missing from {start_str} to {end_str}, count: {delta / 1000 - 1:.0f}")
                    missing_tick += [(start_tick, end_tick)]

        return all_data,missing_tick

    def start_multi_thread(self,sn,start, end):
        start_str = datetime.datetime.fromtimestamp(start / 1000).strftime('%Y-%m-%d %H:%M:%S')
        end_str = datetime.datetime.fromtimestamp(end / 1000).strftime('%Y-%m-%d %H:%M:%S')
        self.Print_log('此轮下载的开始时间:'+start_str+'  结束时间'+end_str)
        min_start = time.time()
        threads = []
        time_slice = self.cut_time(start, end)
        for i in range(len(time_slice)):
            slice_start = time_slice[i]
            thread = myThread(i, 'thread-1'+str(i),sn,slice_start[0],slice_start[1],self.app_id)
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join()
        global every_hour_data
        self.Print_log(f"此轮的数据条数= {len(every_hour_data)}")
        ecg_hour_data = every_hour_data
        every_hour_data = []
        ecg_hour_data.sort(key=lambda f: f["recordTime"])

        if self.write_path != '':
            snId = sn.replace("/", "%2F")
            file_name = os.path.join(self.write_path, f"{snId}_{start}_{end}.txt")
            self.Print_log(file_name)
            if os.path.exists(file_name):
                self.Print_log(f"{file_name} exists, skip downloading")
                with open(file_name) as input:
                    return json.load(input)

            with open(file_name, "a+") as output:
                for line_dict in ecg_hour_data:
                    json.dump(line_dict,output)
                    output.write('\n')
                output.close()

        diff_time = time.time()-min_start
        self.Print_log(f'耗时{int(diff_time)}S  继续下一轮')
        return ecg_hour_data

    #从java封装的接口下载
    def download_single(self, sn, start, end):
        snId = sn
        sn = sn.replace("/", "%2F")

        try:
            start_time = time.time()
            query_param_dict = {
                "sensorId": snId,
                "start": int(start),
                # start_millis to end_millis is a closed interval
                "end": int(end),
            }
            headers_dict = {
                "accessKey": "sejefpnsddsn",
                "secretKey": "psttZOf3UwBr3jdH"
            }
            base_url = "https://cardiac.vivalnk.com/api/data/full_ecg"
            start = time.time()
            response = requests.get(base_url, params=query_param_dict, headers=headers_dict)
            self.Print_log(f"elapsed time: {time.time() - start_time:.0f} seconds to fetch")
            result = response.content
            try:
                json_data = json.loads(result)
                if json_data["code"] != 200:
                    self.Print_log("failed:", json_data["code"], json_data["message"])
                    return None
            except Exception as e:
                self.Print_log("failed to load json string")
                self.Print_log(e)
                self.Print_log(result)

            data_part = json_data["data"]

            self.Print_log('数据长度:' + str(len(data_part)))

            if self.write_path != '':
                file_name = os.path.join(self.write_path, f"{sn}_{start}_{end}.txt")
                self.Print_log(file_name)
                if os.path.exists(file_name):
                    print(f"{file_name} exists, skip downloading")
                    with open(file_name) as input:
                        return json.load(input)

                with open(file_name, "w") as output:
                    json.dump(data_part, output)
                    output.close()

        except Exception as e:
            self.Print_log(e)

        return data_part

    def cut_time(self,start, end):
        time_slice = []
        it = start
        while it < end:
            new_end = it + 60 * 1000 - 1
            if end <= new_end:
                time_slice.append((it, end))
                break
            else:
                time_slice.append((it, new_end))
                it = new_end + 1
        return time_slice


class myThread (threading.Thread):
    def __init__(self, threadID, name,sn,start_time,end_time,appid):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.sn = sn
        self.appid = appid


    def run(self):
        # print ("开启线程：" + self.name)
        returnContent = self.download_ecg_from_vCloud_thread(self.sn,self.start_time,self.end_time)
        if returnContent == 'error':
            request_param = {}
            request_param['st'] = self.start_time
            request_param['et'] = self.end_time
            request_param['threadName'] = self.name
            download_error.append(request_param)
        # print ("退出线程：" + self.name)

    def download_ecg_from_vCloud_thread(self,sn, dl_start, dl_end):

        query_param_dict = {
            "sensorid": sn,
            "appId": self.appid,
            'type': "EcgRaw",
            "start": dl_start,
            "end": dl_end,
        }
        base_url = "https://zciwpugh35.execute-api.ap-south-1.amazonaws.com/test/eventList"

        try:
            response = requests.get(base_url, params=query_param_dict)
        except Exception as e:
            print(e)
            return 'error'
        if response is None:
            print('response为空')
            return 'None'
        json_dict = json.loads(response.content)
        json_data = json_dict["data"]
        if len(json_data) == 0:
            return 'None'
        # print('start:' + str(dl_start) + '  ' + 'end:' + str(dl_end))
        # print(len(json_data))
        for data_dict in json_data:
            record_time = data_dict['recordTime']
            ecg_json = data_dict['data']
            ecg_json['recordTime'] = record_time
            ecg_json['receiveTime'] = data_dict['receiveTime']
            every_hour_data.append(ecg_json)


class ECGThread (threading.Thread):
    def __init__(self,threadID,name,sn,start_time,end_time):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.sn = sn

    def run(self):
        print ("开启线程：" + self.name)
        self.download_ecg_from_java_api()
        print ("退出线程：" + self.name)


    def download_ecg_from_java_api(self):
        start_time = time.time()
        query_param_dict = {
            "sensorId": self.sn,
            "start": int(self.start_time),
            # start_millis to end_millis is a closed interval
            "end": int(self.end_time),
        }
        headers_dict = {
            "accessKey": "sejefpnsddsn",
            "secretKey": "psttZOf3UwBr3jdH"
        }
        base_url = "https://cardiac.vivalnk.com/api/data/full_ecg"
        response = requests.get(base_url, params=query_param_dict, headers=headers_dict)
        result = response.content
        # print(result)
        print(f"elapsed time: {time.time() - start_time:.0f} seconds to fetch")
        try:
            json_dict = json.loads(result)
            if json_dict["code"] != 200:
                print("failed:", json_dict["code"], json_dict["message"])
                return 'None'
            else:
                json_data = json_dict["data"]
                if len(json_data) == 0:
                    return 'None'
                for data_dict in json_data:
                    # record_time = data_dict['recordTime']
                    # ecg_json = data_dict['data']
                    # ecg_json['recordTime'] = record_time
                    # ecg_json['receiveTime'] = data_dict['receiveTime']
                    every_hour_data.append(data_dict)
        except Exception as e:
            print("failed to load json string")
            print(e)
            return 'None'