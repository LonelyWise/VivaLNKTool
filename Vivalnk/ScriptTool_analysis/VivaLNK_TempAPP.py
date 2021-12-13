#!/usr/bin/env python 
# coding:utf-8

import requests
import hashlib
import time
import json
import os

class DownloadTemp:
    def __init__(self,write_path,Download_Temp_Log):
        self.write_path = write_path
        self.Download_Temp_Log = Download_Temp_Log

    def download_temp_foreign(self,sn,start_time,end_time,location,type):
        '''
        下载国外服务器温度数据,缓存设备温度数据
        :param sn: 设备号
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param location: 是否返回定位信息
        :param type: 0是原始温度  1是算法温度  2是两种温度都返回
        :return: json的体温数据
        '''
        host = "http://cadent.us-west-1.elasticbeanstalk.com"
        base_url = host + "/ohin1/api/fever_scout/temperature"
        temp_data = self.download_temp_request(base_url,sn,start_time,end_time,location,type)

        return temp_data

    def download_temp_domestic(self,sn,start_time,end_time,location,type):
        '''
        下载国内服务器温度数据
        :param sn: 设备号
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param location: 是否返回定位信息
        :param type: 0是原始温度  1是算法温度  2是两种温度都返回
        :return:
        '''
        host = "http://ohin1.cn-northwest-1.eb.amazonaws.com.cn"
        base_url = host + "/api/fever_scout/temperature"

        temp_data = self.download_temp_request(base_url,sn,start_time,end_time,location,type)
        return temp_data


    def download_temp_request(self,url,sn,start_time,end_time,location,type):
        # snID = sn.replace(".", "_")
        snID = sn
        query_param_dict = {
            "device_sn": sn,
            "start_millis": start_time,
            # start_millis to end_millis is a closed interval
            "end_millis": end_time,
            # 是否上传经纬度
            "location": location,
            "type": type
        }
        self.Download_Temp_Log(query_param_dict)
        secret_key = "Dr4AYxlucfju1FLuonJNkH1Y+K23Xij3"
        headers_dict = {
            "accessKey": "eyxsPS67mtB7EoTKOcE5tE4Fu"
        }

        query_param_dict = self.generate_query_params(query_param_dict, secret_key)
        start = time.time()
        response = requests.get(url, params=query_param_dict, headers=headers_dict)
        self.Download_Temp_Log(f"Completed in {round(time.time() - start, 3)} seconds")
        # print(response.content)
        json_dict = json.loads(response.content)
        json_data = json_dict["data"]
        json_temp = json_data["temperatures"]

        json_temp.sort(key=lambda f: f["recordTime"])
        if self.write_path != '':
            file_name = os.path.join(self.write_path, f"{snID}_{start_time}_{end_time}.log")
            self.Download_Temp_Log('温度数据存储在:'+file_name)
            if os.path.exists(file_name):
                print(f"{file_name} exists")
                with open(file_name) as input:
                    return json.load(input)

            with open(file_name, "w") as output:
                json.dump(json_temp, output)
                output.close()
        else:
            self.Download_Temp_Log('没有选择存储的文件夹')
        return json_temp

    def generate_signature(self,query_param_dict, secret_key):
        target_str = ''
        # Concatenate the parameters in ascending order of key
        sorted_key = sorted(query_param_dict.keys())
        for key in sorted_key:
            target_str += f"&{key}={query_param_dict[key]}"
        # Remove the first character '&'
        target_str = target_str[1:]
        # Append secret key
        target_str += secret_key
        md5 = hashlib.md5()
        md5.update(target_str.encode(encoding='utf-8'))
        return md5.hexdigest()

    def generate_query_params(self,query_param_dict, secret_key):
        sign = self.generate_signature(query_param_dict, secret_key)
        query_param_dict["sign"] = sign
        return query_param_dict

