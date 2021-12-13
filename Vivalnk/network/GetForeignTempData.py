#!/usr/bin/env python 
# coding:utf-8
'''
下载国外服务器上的体温数据
FeverScout、Cadent的APP数据上传的服务器
'''

import hashlib
import time
import requests
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_signature(query_param_dict, secret_key):
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


def generate_query_params(query_param_dict, secret_key):
    sign = generate_signature(query_param_dict, secret_key)
    query_param_dict["sign"] = sign
    return query_param_dict


def download_temp_request():
    query_param_dict = {
        "device_sn": "B33.00032672",
        "start_millis": 1598508600000,
        # start_millis to end_millis is a closed interval
        "end_millis": 1598512200000,
        # 是否上传经纬度
        "location": False,
        # type 0是原始温度  1是算法温度  2是两种温度都返回
        "type": 0
    }

    secret_key = "Dr4AYxlucfju1FLuonJNkH1Y+K23Xij3"
    headers_dict = {
        "accessKey": "eyxsPS67mtB7EoTKOcE5tE4Fu"
    }

    host = "http://cadent.us-west-1.elasticbeanstalk.com"
    base_url = host + "/ohin1/api/fever_scout/temperature"
    query_param_dict = generate_query_params(query_param_dict, secret_key)
    start = time.time()
    response = requests.get(base_url, params=query_param_dict, headers=headers_dict)
    print(f"Completed in {round(time.time() - start, 3)} seconds")
    # print(response.content)
    json_dict = json.loads(response.content)
    json_data = json_dict["data"]
    json_temp = json_data["temperatures"]

    json_temp.sort(key=lambda f: f["recordTime"])
    print(json_temp)
    return json_temp


def draw_temp_waveform(temp_data):
    # temp_array = []
    # time_array = []
    #
    #
    # for temp_dict in temp_data:
    #     # temp_time = temp_dict["recordTime"] / 1000
    #     # timeArray = time.localtime(temp_time)
    #     # time_format = time.strftime("%H:%M:%S", timeArray)
    #     time_format = np.datetime64(temp_dict["recordTime"], "ms") +  np.timedelta64(8, "h")
    #     time_array.append(time_format)
    #     #温度
    #     temp = temp_dict["raw"]
    #     temp_array.append(temp)

    # x_array = []
    # x_count = 0
    # for j in time_array:
    #     x_array.append(x_count);
    #     x_count += 1

    # pltecg = plt.subplot(2, 1, 1)
    # plt.sca(pltecg)
    # x = np.linspace(0, len(temp_array), len(temp_array), endpoint=True)

    # plt.rcParams['font.sans-serif'] = ['SimHei']  # 可以解释中文无法显示的问题
    # plt.plot(time_array, temp_array, label='temp')
    # plt.xticks(x_array, time_array)
    # plt.xticks(rotation=90)
    hr_x = np.array([np.datetime64(i["recordTime"], "ms") + np.timedelta64(8, "h") for i in temp_data])
    hr_y = [i["raw"] for i in temp_data]
    ax = plt.subplot(111)

    plt.title("Temp")
    plt.ylim(10, 38)
    ax.set_yticks(np.arange(10, 38, 1))
    # plt.grid()
    plt.plot(hr_x, hr_y,'o-')
    plt.axhline(35.5, linestyle="--", color="red")
    plt.axhline(37.5, linestyle="--", color="red")

    # plt.xlabel("Times")
    # plt.ylabel("Temp")
    # plt.title("Temp Wave")
    #
    # plt.ylim(20.0, 39.0)

    plt.legend()  # 显示左下角的图例

    plt.show()
if __name__ == '__main__':
    json_temperatures = download_temp_request()
    draw_temp_waveform(json_temperatures)
