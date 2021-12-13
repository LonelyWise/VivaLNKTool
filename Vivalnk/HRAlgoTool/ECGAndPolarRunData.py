#!/usr/bin/env python 
# coding:utf-8
'''
使用patch运动采集的数据和polar数据对比绘制图形
'''


import json
import datetime
import matplotlib.pyplot as plt
import numpy as np

def sort_data():
    all_data = []
    all_data1 = []
    ecg_start_time1 = 1600240620000 # 2020-09-16 15:17:00
    ecg_end_time1 = 1600240920000   # 2020-09-16 15:22:00
    all_data2 = []
    ecg_start_time2 = 1600241040000 # 2020-09-16 15:24:00
    ecg_end_time2 = 1600241160000   # 2020-09-16 15:26:00
    all_data3 = []
    ecg_start_time3 = 1600241700000 # 2020-09-16 15:35:00
    ecg_end_time3 = 1600241959000   # 2020-09-16 15:41:00

    with open('/Users/xuwei/Desktop/renbinqi跑步数据/VVDeviceDataLog 2020-09-16 15-08.log') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break

            index = lines.index("{")
            lines = lines[index:len(lines)]
            json_dict = json.loads(lines)
            recordTime = json_dict["recordTime"]
            hr_value = json_dict['hr']
            if recordTime >= ecg_start_time1 and recordTime <= ecg_end_time1:
                all_data1.append(hr_value)
            elif recordTime >= ecg_start_time2 and recordTime <= ecg_end_time2:
                all_data2.append(hr_value)
            elif recordTime >= ecg_start_time3 and recordTime <= ecg_end_time3:
                all_data3.append(hr_value)

            if recordTime >= ecg_start_time1 and recordTime <= ecg_end_time3:
                all_data.append(hr_value)
    # all_data.sort(key=lambda f: f["recordTime"])

    # for i in range(len(all_data) - 1):
    #     end_tick = all_data[i + 1]["recordTime"]
    #     start_tick = all_data[i]["recordTime"]
    #     delta = end_tick - start_tick
    #     start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
    #     end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
    #
    #     if abs(delta) < 500:
    #         print(f"duplicated from {start_str} to {end_str}")
    #
    #     if delta > 1100:
    #         print(f"part one: missing from {start_str} to {end_str}, count: {delta / 1000 - 1:.0f}")


    # with open('/Users/xuwei/Desktop/renbinqi跑步数据/process.log', "w") as output:
    #     json.dump(all_data, output)
    #     output.close()
    polar_hr_data = []
    polar_hr_data1 = []
    polar_hr_data2 = []
    polar_hr_data3 = []
    line_num = 0
    polar_recordTime = 1600239787000+100000
    with open('/Users/xuwei/Desktop/renbinqi跑步数据/Charley_Luo_2020-09-16_15-03-07.CSV') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break
            line_num = line_num + 1
            if line_num >= 4:
                polar_array = lines.split(',')
                polar_recordTime = polar_recordTime + 1000
                print(polar_recordTime)
                polar_hr = int(polar_array[2])
                if polar_recordTime >= ecg_start_time1 and polar_recordTime <= ecg_end_time1:
                    polar_hr_data1.append(polar_hr)
                elif polar_recordTime >= ecg_start_time2 and polar_recordTime <= ecg_end_time2:
                    polar_hr_data2.append(polar_hr)
                elif polar_recordTime >= ecg_start_time3 and polar_recordTime <= ecg_end_time3:
                    polar_hr_data3.append(polar_hr)

                if polar_recordTime >= ecg_start_time1 and polar_recordTime <= ecg_end_time3:
                    polar_hr_data.append(polar_hr)


    polar_x = np.linspace(0, 1, len(polar_hr_data2))
    ecg_x = np.linspace(0, 1, len(all_data2))
    polar_label = 'polar' + '\n' + 'HR Count=' + str(len(polar_hr_data2))
    plt.plot(polar_x, polar_hr_data2, label=polar_label)
    vivalnk_label = 'VivaLNK' + '\n' + 'HR Count=' + str(len(all_data2))
    plt.plot(ecg_x, all_data2, label=vivalnk_label)
    plt.ylim(-5, 250)

    save_path = '/Users/xuwei/Desktop/renbinqi跑步数据/' + '002' + '.png'
    plt.legend(loc=0)  # 显示左下角的图例
    plt.savefig(save_path)
    plt.show()




    print('sss')

if __name__ == "__main__":
    sort_data()