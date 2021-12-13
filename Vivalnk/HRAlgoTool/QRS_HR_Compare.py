# 对比QRS算法V1.0.10和V1.0.11的结果
# 用于HR翻倍上升时两个算法的对比

import numpy as np
from ScriptTool_analysis.VivaLNK_Reading import ReadFile
import matplotlib.pyplot as plt
from matplotlib import ticker

TIME_ZONE = np.timedelta64(8, "h")
def print_msg(msg):
    print(msg)


def get_data(file_path1,file_path2):

    read_file = ReadFile(print_msg)
    all_data,miss,type = read_file.read_file_data(file_path1)
    all_data1, miss1, type1 = read_file.read_file_data(file_path2)

    hr_array = []
    for dict in all_data:
        hr = dict["hr"]
        hr_array.append(hr)

    hr1_array = []
    for dict in all_data1:
        hr = dict["hr"]
        hr1_array.append(hr)

    hr_x_time = np.array([np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in all_data])

    raw_ecg_x = [np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in all_data]
    raw_ecg_y = [i["ecg"] for i in all_data]
    rwl_x = []
    rwl_y = []
    ecg_x = []
    ecg_y = []
    for i in range(len(raw_ecg_x)):
        for j in range(128):
            raw_x = raw_ecg_x[i] + np.timedelta64(int(j * 1000 / 128), "ms")
            raw_y = raw_ecg_y[i][j]
            ecg_x.append(raw_x)
            ecg_y.append(int(raw_y))

    new_ecg_y = np.array(ecg_y)


    return hr_x_time,hr_array,hr1_array,ecg_x,new_ecg_y


def draw_data(hr_x_time,hr1,hr2,ecg_x_time,ecg):
    plt.figure()
    hr_ax = plt.subplot(2, 1, 1)
    plt.ylim(-10, 310)
    plt.plot(hr_x_time, hr1, label="V1.0.10")
    plt.plot(hr_x_time, hr2, label="V1.0.11")
    plt.legend()


    ecg_ax = plt.subplot(212,sharex=hr_ax)
    plt.ylim(-5000, 5000)
    formatter = ticker.FuncFormatter(lambda x, y: f"{x / 1000:.3}mV")
    ecg_ax.yaxis.set_major_formatter(formatter)


    plt.plot(ecg_x_time, ecg)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    hr_time,hr10,hr11,ecg_time,ecg_array = get_data('/Users/weixu/Desktop/V10.log','/Users/weixu/Desktop/V11.log')
    draw_data(hr_time,hr10,hr11,ecg_time,ecg_array)