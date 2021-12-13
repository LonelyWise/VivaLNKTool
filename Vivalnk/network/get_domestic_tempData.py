#!/usr/bin/env python
# coding:utf-8
'''
下载国内服务器上的体温数据
感之度体温的APP数据上传的服务器
'''


import hashlib
import time
import requests

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

if __name__ == '__main__':
    query_param_dict = {
        "device_sn": "F13.00150008",
        "start_millis": 1592360880000,
        # start_millis to end_millis is a closed interval
        "end_millis": 1592364600000,
        "location": False,
        "type": 0
    }
    secret_key = "Dr4AYxlucfju1FLuonJNkH1Y+K23Xij3"
    headers_dict = {
        "accessKey": "eyxsPS67mtB7EoTKOcE5tE4Fu"
    }

    host = "http://ohin1.cn-northwest-1.eb.amazonaws.com.cn"
    base_url = host + "/api/fever_scout/temperature"
    print("URL:" + base_url)
    query_param_dict = generate_query_params(query_param_dict, secret_key)
    print("query_param_dict:")
    print(query_param_dict)
    start = time.time()
    response = requests.get(base_url, params=query_param_dict, headers=headers_dict)
    print(f"Completed in {round(time.time() - start, 3)} seconds")
    print(response.content)
