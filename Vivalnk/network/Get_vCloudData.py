#!/usr/bin/env python 
# coding:utf-8
'''
VivaLNk SDK数据才会上传到vCloud
从vcloud上下载血氧和体温数据的测试
'''
import requests
import time
import json


def download_data_from_vcloud(sn,dl_start,dl_end):
    type = "TemperatureRaw"
    if sn.find('O2') >= 0:
        type = "SpO2Raw"

    query_param_dict = {
        "sensorid": sn,
        "appId": 'com.vivalnk.mvm',
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


def cut_time(start,end):
    time_slice = []
    it = start
    while it < end:
        new_end = it + 60*1000 - 1
        if end <= new_end:
            time_slice.append((it, end))
            break
        else:
            time_slice.append((it, new_end))
            it = new_end + 1
    return time_slice


if __name__ == '__main__':

    time_slice = cut_time(1600066200000,1600066200000+60*1000*10)
    print(time_slice)

    json_array = []
    for i in time_slice:
        print('start = ' + str(i[0]))
        print('end = ' + str(i[1]))
        json_data = download_data_from_vcloud('O2 9903',i[0],i[1])
        if json_data is None:
            print('None')
            continue
        print(len(json_data))
        for data_dict in json_data:
            universal_json = data_dict['data']
            json_array.append(universal_json)

    print(json_array)
