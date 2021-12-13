#!/usr/bin/env python 
# coding:utf-8

import urllib.request
import json
from urllib.parse import quote


url = 'http://localhost:8886'

music_url = 'https://www.sojson.com/api/qqmusic/8446666'
weather_url = 'http://t.weather.sojson.com/api/weather/city/101210101'
calendar_url = 'https://www.sojson.com/open/api/lunar/json.shtml'
robot_url = 'http://api.qingyunke.com/api.php?key=free&appid=0&msg='

try:
    # 请求
    resu = urllib.request.urlopen(url, data=None, timeout=10)
    print(resu.headers)
    data = resu.read()
    # print(data)
    # 指定编码请求
    data_decode = data.decode('utf-8')
    print('使用解码:' + data_decode)

    print('状态码:' + str(resu.status))
except:
    print ('请求数据异常')
else:
    print ('请求成功')

def request_data_use_with():
    # 指定编码请求
    with urllib.request.urlopen(url) as resu:
        print(resu.read(300).decode('GBK'))


#天气API数据
def requet_json_data(url):
    with urllib.request.urlopen(url) as resu:
        json_data = resu.read()
        json_data_decode = json_data.decode('utf-8')
        # print(json_data_decode)
        json_dict = json.loads(json_data_decode)
        # print(json_dict)

        for key in json_dict.keys():
            print('key = ' + key)
            json_value = json_dict[key]
            # print(json_value)
            print('value = ' + str(json_dict[key]))



if __name__ == '__main__':
    print('main')
    # request_data_use_with()
# 音乐API
    requet_json_data(music_url)
# 天气API
    requet_json_data(weather_url)
# 日历API
    requet_json_data(calendar_url)
# 智能机器人API
    msg = '天气杭州'
    # 将中文改成url编码
    print(quote(msg))
    assembel_url = robot_url + quote(msg)
    print(assembel_url)
    requet_json_data(assembel_url)

