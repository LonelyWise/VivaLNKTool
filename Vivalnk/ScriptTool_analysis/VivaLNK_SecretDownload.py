#!/usr/bin/env python
# coding:utf-8
import requests
import json
import datetime
import time
import os
import sys
import configparser


SDK_Version = ''
Patch_info = ''

class SecretDownload:
    def __init__(self,write_path, Download_Log, secret_id_value, secret_key_value):
        self.write_path = write_path
        self.Download_Log = Download_Log
        self.secret_id_value = secret_id_value
        self.secret_key_value = secret_key_value
        self.download_token = ''
        self.download_path = ''
        self.download_host = ''
        self.auth_path = ''
        self.MsgFilePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'MsgFile')
        self.iniPath = os.path.join(self.MsgFilePath, 'AppConfig.ini')

    # 下载数据增加鉴权的新接口
    def getToken(self):
        headers_dict = {
            'Content-Type':"application/json"
        }

        params_dict = {}
        params_dict['id'] = self.secret_id_value
        params_dict['key'] = self.secret_key_value
        params_dict_str = json.dumps(params_dict)
        print(params_dict)
        try:
            response = requests.post(url=self.download_host+self.auth_path, data=params_dict_str, headers=headers_dict)
        except Exception as e:
            self.Download_Log(e)
            return None

        result = json.loads(response.content)
        if result['code'] == 200:
            self.download_token = result['data']['token']
            print(self.download_token)

            return self.download_token
        else:
            self.Download_Log('token获取失败'+json.dumps(result))
            self.Download_Log('id和key的值错误，请导入正确的值')
            return None

    # 时间切割及数据返回下载返回后的分析
    def before_download_cut_time(self, deviceType, deviceSn, startTime, endTime):
        cut_section = 3600
        caculate_miss = 1
        miss_mill_scope = 1050
        if deviceType == 'ECG':
            pass
        elif deviceType == 'Temp':
            cut_section = 24*3600
            # 目前F开头的都是VV200-6的
            if deviceSn.find('F') >= 0:
                caculate_miss = 12
                miss_mill_scope = 25000
            else:
                caculate_miss = 16
                miss_mill_scope = 33000

        elif deviceType == "SpO2":
            cut_section = 2*3600
            caculate_miss = 4
            miss_mill_scope = 4500
        elif deviceType == 'BP':
            cut_section = 168*3600

        hour_time_slice = self.cut_time_slice(startTime, endTime, cut_section)

        print(hour_time_slice)
        all_data = []
        reqiest_error = 0
        for i in hour_time_slice:
            start_str = datetime.datetime.fromtimestamp(i[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            end_str = datetime.datetime.fromtimestamp(i[1] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            self.Download_Log('download interval - start time:' + start_str + '  end time:' + end_str)

            data_part = self.download_data_from_secret_api(deviceSn,i[0],i[1])
            if data_part == 'Unauthorized request':
                reqiest_error = 1
                all_data = []
                break
            if data_part is not None:
                all_data += data_part

        if reqiest_error:
            self.download_token = ''
            self.before_download_cut_time(deviceType,deviceSn,startTime,endTime)
            return [],[]

        if len(all_data) == 0:
            self.Download_Log("no data is downloaded")
            return [],[]

        all_data.sort(key=lambda f: f["recordTime"])

        zero_dict = all_data[0]
        # 丢失分析
        if deviceType != 'BP':
            theory_count = (endTime - startTime) / 1000
            theory_count = theory_count/caculate_miss
            self.Download_Log(f"Theoretical number:{theory_count}")
            self.Download_Log(f"Actual number:{len(all_data)}")
            theory_missing = int(theory_count - len(all_data))
            self.Download_Log(f"Query the number of theoretical losses in the time range: {theory_missing}")
            scope_count = (all_data[len(all_data) - 1]['recordTime']/1000 - zero_dict['recordTime']/1000)/caculate_miss + 1
            self.Download_Log(f"Query time range actual data start and end lost quantity: {int(scope_count) - len(all_data)}")

        global SDK_Version
        global Patch_info
        self.Download_Log(f"SDK Version:{SDK_Version}")
        self.Download_Log(f"Device Info:{Patch_info}")
        min_receive = 0
        max_receive = 0

        # 丢失列表
        missing_tick = []
        for i in range(len(all_data) - 1):
            # 实时血氧数据不参与丢失分析
            flash = all_data[i]['flash']
            if deviceType == "SpO2":
                if flash == 0:
                    continue

            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
            end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')

            receive_time = all_data[i]['receiveTime']
            if min_receive == 0:
                min_receive = receive_time
                max_receive = receive_time
            else:
                if receive_time < min_receive:
                    min_receive = receive_time
                if receive_time > max_receive:
                    max_receive = receive_time

            if abs(delta) < 500:
                self.Download_Log(f"duplicated from {start_str} to {end_str}")

            if delta > miss_mill_scope:
                self.Download_Log(f"part one: missing from {start_str} to {end_str}, count: {(delta / 1000)/caculate_miss - 1:.0f}")
                missing_tick += [(start_tick, end_tick)]

        # 这段数据上传所用的时间
        min_receive_str = datetime.datetime.fromtimestamp(min_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
        max_receive_str = datetime.datetime.fromtimestamp(max_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
        total_receivce_time = max_receive - min_receive
        self.Download_Log(f"This piece of data upload server receiving time:{min_receive_str},{max_receive_str},for spending {int(total_receivce_time/1000)} second")

        return all_data,missing_tick
    # 调用下载接口
    def download_data_from_secret_api(self,sn,startTime,endTime):
        # 为空就去调用token下载接口
        if self.download_token == '':
            self.download_token = self.getToken()
            if self.download_token is None:
                return
            config = configparser.ConfigParser()
            config.read(self.iniPath)
            config.set('Download.config','token',self.download_token)
            with open(self.iniPath,'w') as configFile:
                config.write(configFile)

        headers_dict = {
            'Content-Type': "application/json",
            'Authorization':self.download_token
        }
        params_dict = {
            'patchSn':sn,
            'startTime':startTime,
            'endTime':endTime,
        }
        record_request_time = time.time()
        try:

            response = requests.get(self.download_host+self.download_path,params=params_dict,headers = headers_dict)
        except Exception as e:
            self.Download_Log(e)
            return None
        self.Download_Log(f"Download time: {time.time() - record_request_time:.0f} second")

        result_dict = json.loads(response.content)

        if 'errorMessage' in result_dict:
            self.Download_Log(result_dict['errorMessage'])
            return None

        all_data_vitals = []
        if 'code' not in result_dict:
            return 'Unauthorized request'
        if result_dict['code'] == 200:
            data_dict = result_dict['data']
            data_list = data_dict['list']
            self.Download_Log('Data Length:' + str(len(data_list)))
            if len(data_list) == 0:
                return None
            zero_list = data_list[0]
            global SDK_Version
            global Patch_info
            if 'sdkVersion' in zero_list:
                SDK_Version = zero_list['sdkVersion']
            if 'patchInfo' in zero_list:
                Patch_info = zero_list['patchInfo']

            for list_dict in data_list:
                data_vitals = list_dict['vitals']
                data_vitals['recordTime'] = list_dict['recordTime']
                data_vitals['receiveTime'] = list_dict['receiveTime']
                data_vitals['deviceName'] = sn
                data_vitals['battery'] = list_dict['patchBattery']
                all_data_vitals.append(data_vitals)

            sn = sn.replace('/', '%2f')
            if self.write_path != '':
                startTime_str = datetime.datetime.fromtimestamp(startTime / 1000).strftime('%Y-%m-%d %H-%M-%S')
                endTime_str = datetime.datetime.fromtimestamp(endTime / 1000).strftime('%H-%M-%S')
                file_name = os.path.join(self.write_path, f"{sn}_{startTime_str}_{endTime_str}.txt")
                self.Download_Log(file_name)
                if os.path.exists(file_name):
                    print(f"{file_name} exists, skip downloading")
                else:
                    with open(file_name, "a+") as output:
                        for line_dict in all_data_vitals:
                            line_time_str = datetime.datetime.fromtimestamp(line_dict['recordTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                            lines_str = line_time_str+":"+json.dumps(line_dict)+'\n'
                            # json.dump(line_dict, output)
                            output.write(lines_str)
                        output.close()
            return all_data_vitals
        else:
            self.Download_Log(json.dumps(result_dict))
            if result_dict['code'] == 401:
                return 'Unauthorized request'
            else:
                return 'error'

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

# 单元测试接口
def print_msg(msg):
    print(msg)

def read_request_msg(filename):
    with open(filename,'r') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break
            json_dict = json.loads(lines)
            print_msg(json_dict)
            return json_dict

if __name__ == "__main__":
    # down = SecretDownload('/Users/cyanxu/Documents/维灵/ECG数据/TestNewAPI/',print_msg)
    # down.before_download_cut_time('ECG','ECGRec_202043/C710095',1611565200000,1611568799000)
    # down.before_download_cut_time('SpO2','O2 9784',startTime=1611656640000,endTime=1611656640000+60*1000*1)
    # down.before_download_cut_time('Temp','C01.00006575',1611572700000,1611572700000+60*1000*10)


    # jsdict = read_request_msg('./MsgFile/secret.txt')
    # print_msg(json.dumps(jsdict))

    # write_request_msg('./MsgFile/secret.txt','','')

    # token = read_request_token('./MsgFile/token.txt')
    # print_msg(token)

    params_dict = "{\"id\": \"3a6a7700c57f4f26a2ec4b0a3\",\"key\": \"h^JHhAPQ4Z^^b5_itTnprO34uP^;OaBAT1_ydli>\"}"
    params_dict1 = {}
    params_dict1["id"] = "3a6a7700c57f4f26a2ec4b0a3"
    params_dict1["key"] = "h^JHhAPQ4Z^^b5_itTnprO34uP^;OaBAT1_ydli>"
    print(params_dict)
    print_msg(json.dumps(params_dict1))