#!/usr/bin/env python 
# coding:utf-8


import wfdb
from wfdb.plot import plot_wfdb
import os
import matplotlib.pyplot as plt
import numpy as np
import time
import datetime
from ScriptTool_analysis.VivaLNK_ProcessMedicalFile import ProcessMitData

mit16_dir_path = '/Users/weixu/Documents/暂时存放-可删/mit16'

record_name = 'nalong-1620694800000'

# 生成mit16数据函数
# wfdb.wrsamp()

record_name_path = os.path.join(mit16_dir_path, record_name)

record = wfdb.rdrecord(record_name_path)
print(record.__dict__)
p_signal = record.p_signal


diff = (1620774300 - 1620694800)*128
end = diff+60*128

new_signal = p_signal[diff:end]
ecg_buffer = []
for value in new_signal:
    ecg_buffer.append(int(value[0]*1000))

ecg_all = []
ecg_all.append(ecg_buffer)


mit_path = os.path.join('/Users/weixu/Documents/暂时存放-可删','new_mit16')
if not os.path.exists(mit_path):
    os.makedirs(mit_path, exist_ok=True)
def printLog(msg):
    print(msg)

mit16_start_time = 1620774300
process_mit = ProcessMitData(mit_log=printLog)
process_mit.generate_mit_file('VivaLNK' + '-' + str(mit16_start_time), 128, [1000], ecg_all,mit16_start_time, None, mit_path)





# start_time = record.base_time
# start_date_time = record.base_datetime
# print(start_date_time)
# print(start_time)
#
# timeStamp = int(time.mktime(start_date_time.timetuple()))


# ecg_array = []
# x_array = []
# time_array = []
# x_count = 1
# time_array.append(start_date_time)
# count_ttt = 0
# for data in p_signal:
#     x_count += 1
#     ecg_array.append(data[0])
#     if x_count == 128:
#         x_count = 1
#
#         timeStamp += 1
#
#         time_inco = datetime.datetime.fromtimestamp(timeStamp)
#         # otherStyleTime = time.strftime("%Y--%m--%d %H:%M:%S", time.localtime(timeStamp))
#         time_array.append(time_inco)
#         count_ttt += 1
#         if count_ttt >= 100:
#             break;
#
#
# x_lenth = len(ecg_array) / 128
#
# x_count = 1
# for j in time_array:
#     x_array.append(x_count);
#     x_count += 1
#
# x = np.linspace(0, x_lenth, len(ecg_array), endpoint=True)
#
# # plt.rcParams['font.sans-serif'] = ['SimHei']#可以解释中文无法显示的问题
# plt.plot(x, ecg_array, label = 'ecg')
# plt.xticks(x_array, time_array)
# plt.xticks(rotation=45)
#
# plt.xlabel("Times")
# plt.ylabel("ECG")
# plt.title("ECG Wave")
# plt.ylim(-10, 10)
#
# plt.legend()  # 显示左下角的图例
# plt.show()

# wfdb.plot_wfdb(record=record, title='Record data')
# plt.plot(record.p_signal[0: len(p_signal), 0])
# plt.show()

