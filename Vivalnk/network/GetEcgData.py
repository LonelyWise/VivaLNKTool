#!/usr/bin/env python 
# coding:utf-8
'''
从vCloud上下载ECG数据的测试
拿来验证是否有数据,下载大量的数据建议使用ScriptTool的界面化工具
'''

import hashlib
import time
import requests
import json

def generate_signature(query_param_dict):
    target_str = ''
    # Concatenate the parameters in ascending order of key
    sorted_key = sorted(query_param_dict.keys())
    for key in sorted_key:
        target_str += f"&{key}={query_param_dict[key]}"
    # Remove the first character '&'
    target_str = target_str[1:]
    md5 = hashlib.md5()
    md5.update(target_str.encode(encoding='utf-8'))
    return md5.hexdigest()


def generate_query_params(query_param_dict):
    sign = generate_signature(query_param_dict)
    query_param_dict["sign"] = sign
    return query_param_dict

if __name__ == '__main__':

    timeIndex = 1
    query_param_dict = {
        "sensorId": "ECGRec_202002/C839512",
        "start": 1599874486000,
        # start_millis to end_millis is a closed interval
        "end": 1599874486000+1000*60*10,
    }

    headers_dict = {
        "accessKey": "sejefpnsddsn",
        "secretKey": "psttZOf3UwBr3jdH"
    }

    base_url = "https://cardiac.vivalnk.com/api/data/full_ecg"
    # query_param_dict = generate_query_params(query_param_dict)
    print(query_param_dict)
    start = time.time()
    response = requests.get(base_url, params=query_param_dict, headers=headers_dict)
    # print(f"Completed in {round(time.time() - start, 3)} seconds")
    # print(response.content)

    sign_time = 0
    json_dict = json.loads(response.content)
    json_data = json_dict["data"]
    print(len(json_data))
    json_data.sort(key=lambda f: f["recordTime"])

    for json_dic in json_data:
        recordTime = json_dic["recordTime"]
        if sign_time == 0:
            sign_time = recordTime
        else:
            time_difference = recordTime - sign_time

            if time_difference > 1050:
                loacl_time1 = time.localtime(sign_time / 1000)
                time_format_string1 = time.strftime("%Y--%m--%d %H:%M:%S", loacl_time1)
                loacl_time2 = time.localtime(recordTime / 1000)
                time_format_string2 = time.strftime("%Y--%m--%d %H:%M:%S", loacl_time2)
                print('丢失的时间为:'+time_format_string1+'~~'+time_format_string2)
                print('时间戳为:'+str(sign_time)+"   "+str(recordTime))
            sign_time = recordTime


