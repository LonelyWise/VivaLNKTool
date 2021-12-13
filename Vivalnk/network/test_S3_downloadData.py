#!/usr/bin/env python 
# coding:utf-8

import requests
import http.client
import time
import json
import copy
import datetime

def assemble_data(deviceId,recordTime):
    dict = {}
    dict['profileId'] = 'cyan'
    dict['sensorId'] = deviceId
    dict['deviceBattery'] = 100
    dict['receiveTime'] = 0
    dict['deviceToken'] = 'a934e7c50746a5da8085d6203be024168bcaee14'
    dict['sdkVersion'] = '2.1.0'
    dict['latitude'] = 0
    dict['longtitude'] = 0
    dict['deviceIp'] = '10.10.1.45'
    dict['deviceType'] = 'iPhone'
    dict['deviceOsType'] = 'iOS'
    dict['deviceOsVersion'] = '14.0'
    dict['carrier'] = '中国移动'
    dict['networkType'] = '4G'
    dict['language'] = 'zh-Hans-CN'
    dict['timezone'] = '28800'
    dict['patchMessage'] = '1.4.0.0006;06;VIVALNK;VV330;128Hz;ENC;100*10;HR;5Hz;2048'
    dict['app_id'] = 'com.vivalnk.mvm'
    dict['type'] = 'EcgRaw'
    dict["category"] = "not know"
    tag_arr = [{'foo':'val'},{'bar':'val'}]
    dict['tags'] = tag_arr
    context_dic = {'context1':'context data'}
    dict['context'] = context_dic
    dict['auditTrail'] = tag_arr
    dict['name'] = ''
    dict['customData'] = context_dic
    dict['recordTime'] = recordTime
    dict["collectTime"] = recordTime
    #数据组装
    data = {}
    ecg = [-56, -46, -50, -43, -46, -41, -40, -42, -41, -44, -42, -47, -48, -43, -50, -53, -50, -54, -52, -53, -54, -53, -57, -56, -61, -61, -51, -54, -52, -51, -48, -49, -49, -54, -51, -52, -50, -41, -35, -27, -20, -5, -4, -8, -4, -7, -35, -43, -47, -52, -57, -54, -59, -58, -58, -64, -35, 126, 369, 300, -168, -184, -48, 19, 16, 18, 15, 17, 20, 28, 30, 35, 34, 48, 46, 54, 60, 69, 78, 92, 102, 119, 138, 157, 178, 213, 243, 277, 309, 335, 359, 378, 384, 373, 329, 267, 192, 127, 72, 30, 1, -15, -27, -33, -39, -41, -37, -39, -39, -37, -39, -33, -34, -30, -31, -30, -29, -24, -25, -30, -30, -31, -36, -37, -38, -38, -34, -35]
    data['ecg'] = ecg

    acc_array = []
    for i in range(0, 250):
        acc_dict = {}
        acc_dict['x'] = 402
        acc_dict['y'] = -801
        acc_dict['z'] = 1810
        acc_dict['offset'] = 40
        acc_array.append(acc_dict)
    # acc = [{'x':10,'y':100,'z':1000},{'x':10,'y':100,'z':1000},{'x':10,'y':100,'z':1000},{'x':10,'y':100,'z':1000},{'x':10,'y':100,'z':1000}]
    data['acc'] = acc_array
    rri = [1000,0,0,0,0]
    data['rri'] = rri
    rwl = [100,-1,-1,-1,-1]
    data['rwl'] = rwl
    data['leadOn'] = 1
    data['recordTime'] = recordTime
    data['HR'] = 60
    data['RR'] = 10
    data['BP'] = ''
    data['accAccuracy'] = 2048
    data['magnification'] = 1000
    data['flash'] = 0
    data['activity'] = 0
    dict['data'] = data
    return dict


def sendDataToVCloud(payload):
    # print(payload)
    try:
        url = "https://ohez5b65zj.execute-api.ap-south-1.amazonaws.com/production/ingestion"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZW5zb3Jfc24iOiJ0ZXN0NSIsInJlZ19hdHRyaWJ1dGUiOiJhdHRyaWJ1dGUiLCJhcHBfaWQiOiJ2aXZhLXRlc3QiLCJhcHBfa2V5IjoidGVzdF9hcHBfa2V5IiwiZXBvY2hfdHMiOjEwMDAwLCJleHAiOjE2NTY5ODM5ODUsInByaW5jaXBhbCI6InZpdmEtdGVzdCJ9.EbmF4zsZ3TXwq1zZ-2Qha5Q9bdOP3aoanln2R02K1AI'
        }
        response = requests.post(url,json=payload,headers=headers)
        if response.status_code == 200:
            print(json.loads(response.content))
            return True
        else:
            print('发送失败')
            print(response)
            return False
    except Exception as e:
        print(e)
        return False

def assemble_json_data(deviceId):
    url = "https://ohez5b65zj.execute-api.ap-south-1.amazonaws.com/production/ingestion"

    payload = "[\n  {\n    \"app_id\" : \"com.vivalnk.mvm\",\n    \"auditTrail\" : [\n      {\n        \"foo\" : \"val\"\n      },\n      {\n        \"bar\" : \"val\"\n      }\n    ],\n    \"carrier\" : \"中国移动\",\n    \"category\" : \"notknow\",\n    \"collectTime\" : 1573541485444,\n    \"context\" : {\n      \"context1\" : \"contextdata\"\n    },\n    \"customData\" : {\n      \"context1\" : \"contextdata\"\n    },\n    \"data\" : {\n      \"BP\" : \"\",\n      \"HR\" : 247,\n      \"RR\" : 0,\n      \"acc\" : [\n        {\n          \"x\" : -18,\n          \"y\" : 84,\n          \"z\" : -2046\n        },\n        {\n          \"x\" : -17,\n          \"y\" : 88,\n          \"z\" : -2048\n        },\n        {\n          \"x\" : -15,\n          \"y\" : 84,\n          \"z\" : -2048\n        },\n        {\n          \"x\" : -16,\n          \"y\" : 86,\n          \"z\" : -2049\n        },\n        {\n          \"x\" : -17,\n          \"y\" : 94,\n          \"z\" : -2045\n        }\n      ],\n      \"activity\" : false,\n      \"ecg\" : [\n        -2629,\n        -2669,\n        -2647,\n        -2652,\n        -2756,\n        -2765,\n        -2721,\n        -2845,\n        -2797,\n        -2880,\n        -2915,\n        -2876,\n        -2872,\n        -2832,\n        -2903,\n        -2922,\n        -2917,\n        -2887,\n        -2853,\n        -2889,\n        -2956,\n        -2942,\n        -2956,\n        -2888,\n        -2880,\n        -2885,\n        -2859,\n        -2924,\n        -2857,\n        -2815,\n        -2874,\n        -2858,\n        -2848,\n        -2855,\n        -2819,\n        -2938,\n        -2850,\n        -2828,\n        -2911,\n        -2911,\n        -2938,\n        -2904,\n        -2841,\n        -2935,\n        -2855,\n        -2986,\n        -2907,\n        -2947,\n        -2930,\n        -2882,\n        -2987,\n        -2916,\n        -2926,\n        -2991,\n        -2951,\n        -2955,\n        -2991,\n        -2967,\n        -2931,\n        -2950,\n        -3012,\n        -2917,\n        -3018,\n        -2954,\n        -2952,\n        -2932,\n        -2922,\n        -2935,\n        -3079,\n        -2971,\n        -2989,\n        -2967,\n        -3050,\n        -3006,\n        -3025,\n        -3043,\n        -3026,\n        -3012,\n        -3033,\n        -2931,\n        -2754,\n        -2707,\n        -2861,\n        -3543,\n        -3697,\n        -3500,\n        -3284,\n        -3188,\n        -3233,\n        -3231,\n        -3219,\n        -3190,\n        -3204,\n        -3136,\n        -3216,\n        -3248,\n        -3283,\n        -3248,\n        -3195,\n        -3189,\n        -3148,\n        -3139,\n        -3170,\n        -3164,\n        -3199,\n        -3144,\n        -3151,\n        -3112,\n        -3109,\n        -3206,\n        -3162,\n        -3142,\n        -3134,\n        -3123,\n        -3177,\n        -3172,\n        -3222,\n        -3198,\n        -3162,\n        -3304,\n        -3274,\n        -3318,\n        -3378,\n        -3359,\n        -3349,\n        -3364,\n        -3364,\n        -3379\n      ],\n      \"flash\" : true,\n      \"leadOn\" : true,\n      \"magnification\" : 1000,\n      \"rri\" : [\n        0,\n        0,\n        0,\n        0,\n        0\n      ],\n      \"rwl\" : [\n        81,\n        -1,\n        -1,\n        -1,\n        -1\n      ],\n      \"time\" : 1573541312927\n    },\n    \"deviceBattery\" : 100,\n    \"deviceIp\" : \"10.10.1.23\",\n    \"deviceOsType\" : \"iOS\",\n    \"deviceOsVersion\" : \"13.1.3\",\n    \"deviceToken\" : \"a934e7c50746a5da8085d6203be024168bcaee14\",\n    \"deviceType\" : \"iPhone\",\n    \"language\" : \"zh-Hans-CN\",\n    \"latitude\" : 30.180000305175781,\n    \"longtitude\" : 120.22000122070312,\n    \"name\" : \"\",\n    \"networkType\" : \"WiFi\",\n    \"patchMessage\" : \"1.4.0.0006,06,VIVALNK;VV330;128Hz;ENC;100*10;HR;5Hz;2048\",\n    \"profileId\" : \"cyan\",\n    \"receiveTime\" : 0,\n    \"recordTime\" : 1573541312927,\n    \"sdkVersion\" : \"1.3.0\",\n    \"sensorId\" : \"ECGRec_201913/C600018\",\n    \"tags\" : [\n      {\n        \"foo\" : \"val\"\n      },\n      {\n        \"bar\" : \"val\"\n      }\n    ],\n    \"timezone\" : \"28800\",\n    \"type\" : \"EcgRaw\"\n  }\n]"
    data_array = json.loads(payload)
    data_dict = data_array[0]
    content_data = data_dict['data']

    recordTime = int(time.time() * 1000)

    send_array = []
    for i in range(0,1000):
        recordTime += 1000
        data_dict_copy = copy.copy(data_dict)

        data_dict_copy['recordTime'] = recordTime
        data_dict_copy['sensorId'] = deviceId
        send_array.append(data_dict_copy)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzZW5zb3Jfc24iOiJ0ZXN0NSIsInJlZ19hdHRyaWJ1dGUiOiJhdHRyaWJ1dGUiLCJhcHBfaWQiOiJ2aXZhLXRlc3QiLCJhcHBfa2V5IjoidGVzdF9hcHBfa2V5IiwiZXBvY2hfdHMiOjEwMDAwLCJleHAiOjE2NTY5ODM5ODUsInByaW5jaXBhbCI6InZpdmEtdGVzdCJ9.EbmF4zsZ3TXwq1zZ-2Qha5Q9bdOP3aoanln2R02K1AI'
    }

    response = requests.request("POST", url, headers=headers, json=send_array)
    if response.status_code == 200:
        print(json.loads(response.content))
        return True
    else:
        print('发送失败')
        return False

def bind_deviceId_projectId(deviceId,projectId,subjectID):
    print(f'设备号:{deviceId}绑定在{projectId}项目上')
    url = 'https://h0l9dox0g0.execute-api.ap-south-1.amazonaws.com/production/bind-device-tenant'
    data = {
        'tenantName': projectId,
        'deviceId': deviceId,
        'userId': subjectID
    }

    try:
        response = requests.request("POST", url, json=data)
        if response.status_code == 200:
            print(json.loads(response.content))
            success = assemble_json_data(deviceId=deviceId)
            return success
        else:
            print(response)
            return False
    except Exception as e:
        print(e)
        return False

def registerSubject(deviceId,projectId,subjectID):
    url = 'https://8mni95qtb4.execute-api.ap-south-1.amazonaws.com/production/tenant-mode'

    data = {
        'tenantName' : projectId,
        'userId' : subjectID
    }
    print(f'账号{projectId}注册用户名为{subjectID}')
    try:
        response = requests.request("POST", url, json=data)
        if response.status_code == 200:
            print(json.loads(response.content))
            success = bind_deviceId_projectId(deviceId,projectId,subjectID)
            return success
        else:
            print('注册失败')
            return False
    except Exception as e:
        print(e)
        return False

def error_data_reUpload():
    json_str = '{"deviceOsType": "iOS", "collectTime": 1604559143354, "app_id": "com.vivalnk.mvm", "receiveTime": 0, "auditTrail": [{"foo": "val"}, {"bar": "val"}], "sensorId": "ECGRec_202003/C839519", "timezone": "28800", "category": "not know", "recordTime": 1604558551575, "data": {"acc": [{"y": 1232, "x": -1565, "z": 374}, {"y": 1245, "x": -1584, "z": 366}, {"y": 1244, "x": -1583, "z": 388}, {"y": 1251, "x": -1591, "z": 379}, {"y": 1231, "x": -1567, "z": 375}], "ecg": [-28, -16, -19, -20, -10, 29, 166, 396, 475, 263, -314, -611, -509, -344, -178, -26, 2, 16, 36, 53, 54, 58, 68, 78, 88, 96, 104, 119, 117, 133, 138, 153, 162, 174, 194, 206, 233, 254, 272, 289, 316, 332, 343, 345, 351, 341, 308, 276, 233, 187, 136, 100, 70, 38, 32, 23, 15, 12, 6, 13, 7, 15, 15, 16, 17, 20, 20, 20, 26, 21, 23, 13, 14, 11, 12, 13, 6, -1, -2, 5, -1, -2, -1, -3, -4, -14, -9, -17, -16, -24, -9, -17, -19, -8, -9, -4, -2, 2, 3, -4, -2, -8, -2, -13, 1, 5, -6, -12, -2, -4, -12, -3, 5, 5, 14, 26, 33, 14, 12, -1, -11, -20, -22, -35, -39, -28, -30, -31], "accAccuracy": 2048, "RR": 13, "rri": [945, 0, 0, 0, 0], "HR": 60, "flash": true, "rwl": [11, -1, -1, -1, -1], "recordTime": 1604558551575, "magnification": 1000, "leadOn": true, "BP": "", "activity": false}, "patchMessage": "2.1.0.0007,08,VIVALNK;VV330_1;128Hz;ENC;100*10;NOHR;2048", "deviceType": "iPhone", "latitude": 0, "type": "EcgRaw", "deviceToken": "eab904ce3230b53726e5643471eddbe9c87867da", "deviceIp": "10.10.1.65", "tags": [{"foo": "val"}, {"bar": "val"}], "customData": {"context1": "context data"}, "longtitude": 0, "deviceOsVersion": "12.3.1", "networkType": "WiFi", "deviceBattery": 100, "sdkVersion": "2.1.0", "name": "", "language": "zh-Hans-US", "carrier": "\u4e2d\u56fd\u79fb\u52a8", "context": {"context1": "context data"}, "profileId": "cyan"}'

    json_data = json.loads(json_str)

    print(json_data)
    json_array = []
    json_array.append(json_data)
    sendDataToVCloud(json_array)

if __name__ == "__main__":

    # error_data_reUpload()
    # deviceId = "ECGRec_renbinqi-Verily"
    # projectId = "vivalnk-testing-verily"
    # print(f'开始{projectId}项目号的处理')
    # timestamp = time.time()
    # time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    # userId = time_str.replace('-', '')
    # send_status = registerSubject(deviceId, projectId, userId)
    # if send_status:
    #     print(f'{projectId}的数据绑定并且发送成功')
    # else:
    #     print(f'{projectId}的数据发送失败了')
    #
    # deviceId1 = 'ECGRec_renbinqi-UCSF-AF'
    # projectId1 = 'vivalnk-testing-ucsf-af'
    # print(f'开始{projectId1}项目号的处理')
    # userId2 = str(time.strftime("%Y%m%d"))
    # send_status1 = registerSubject(deviceId1, projectId, userId)
    # if send_status1:
    #     print(f'{projectId1}的数据绑定并且发送成功')
    # else:
    #     print(f'{projectId1}的数据发送失败了')
    #
    # deviceId2 = 'ECGRec_renbinqi-Stanford'
    # projectId2 = 'vivalnk-testing-stanford-sleep'
    # print(f'开始{projectId2}项目号的处理')
    # userId3 = str(time.strftime("%Y%m%d"))
    # send_status2 = registerSubject(deviceId2, projectId2, userId)
    # if send_status2:
    #     print(f'{projectId2}的数据绑定并且发送成功')
    # else:
    #     print(f'{projectId2}的数据发送失败了')
    #
    # deviceId3 = 'ECGRec_renbinqi-AFPPG'
    # projectId3 = 'vivalnk-testing-ucsf-afppg'
    # print(f'开始{projectId3}项目号的处理')
    # userId4 = str(time.strftime("%Y%m%d"))
    # send_status3 = registerSubject(deviceId3, projectId3, userId)
    # if send_status3:
    #     print(f'{projectId3}的数据绑定并且发送成功')
    # else:
    #     print(f'{projectId3}的数据发送失败了')


    recordTime = int(time.time() * 1000)
    count = 0
    while (60 - count*10):
        count += 1
        print(count)
        send_array = []
        for i in range(0, 10):
            recordTime += 1000
            print(recordTime)

            data_dict = assemble_data('ECGRec_cyantest', recordTime)
            send_array.append(data_dict)

        sendDataToVCloud(send_array)
        continue




