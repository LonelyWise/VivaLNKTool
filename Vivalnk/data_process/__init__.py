#!/usr/bin/env python 
# coding:utf-8

import os
import json
import sys
from matplotlib import ticker
from scipy.signal import butter, filtfilt
import pyhrv.tools as tools
import pyhrv
import pyhrv.time_domain as td
import pyhrv.frequency_domain as fd
import matplotlib.pyplot as plt
import pyhrv.nonlinear as nl
import time
import datetime
import numpy as np

file_path = '/Users/xuwei/Downloads/55-康泽勇/2020-05-27_09-14-33.json'

TIME_ZONE = np.timedelta64(8, "h")
ECG_HZ = 128
SDNN_DURATION = 300
ACTIVITY_WINDOW = 5*10 # 10 seconds
ACC_HZ = 5
ACTIVITY_SCALE = 50
ENABLE_ECG_ACC = True



def read_data_and_handle():
    all_data = []
    with open(file_path) as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break
            new_lines = lines.replace('}{', '},{')
            new_lines_new = new_lines.replace('},]', '}]')
            all_data = json.loads(new_lines_new)

    new_all_data = []
    for jsonDic in all_data:
        recd_Time = jsonDic["recordTime"]
        if recd_Time > 1590562795000 and recd_Time < 1590562805000:
            new_all_data.append(jsonDic)


    missing = int(3600 - len(new_all_data))
    print(f"totally {missing} seconds missing")
    missing_tick = []

    for i in range(len(new_all_data) - 1):
        end_tick = all_data[i + 1]["recordTime"]
        start_tick = all_data[i]["recordTime"]
        delta = end_tick - start_tick
        start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
        end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')

        if abs(delta) < 500:
            print(f"duplicated from {start_str} to {end_str}")

        if delta > 1100:
            print(f"part one: missing from {start_str} to {end_str}, count: {delta / 1000 - 1:.0f}")
        #     missing_tick += [(start_tick, end_tick)]

    return new_all_data, missing_tick

def extract_feature_python(x, y, z, width=50, Wn=[0.1,0.9]):
    # Center each axis and calculate the total acceleration.
    total = np.sqrt((x - np.mean(x)) ** 2 + (y - np.mean(y)) ** 2 + (z - np.mean(z)) ** 2)

    # Filter the total acceleration.
    b, a = butter(2, Wn, btype="bandpass")
    total = filtfilt(b, a, total)

    feature = np.std(total)

    if feature > 1000:
        return 4
    elif feature > 400:
        return 3
    elif feature > 65:
        return 2
    elif feature > 0:
        return
if __name__ == "__main__":
    all_no_data, missing_tick = read_data_and_handle()

    time_one = all_no_data[0]["recordTime"]

    all_data = []
    for jsonData in all_no_data:
        jsonData["recordTime"] = time_one
        time_one += 1000;
        all_data.append(jsonData)

    time_tttt = 0
    for json_data in all_data:
        record_time = json_data['recordTime']
        if time_tttt == 0:
            time_tttt == record_time
        else:
            diff = record_time - time_tttt
            if diff >= 2000:
                print('xhshsh')
            time_tttt = record_time

    # preprocess ACC
    acc_time = []
    acc_x = []
    for index in range(len(all_data)):
        i = all_data[index]
        acc_hz = len(i["acc"])
        acc_cycle = 1000 / acc_hz
        for index2 in range(acc_hz):
            j = i["acc"][index2]
            acc_x.append(j[0])
            acc_time.append(
                np.datetime64(i["recordTime"], "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2), "ms"))

    acc_y = []
    for i in all_data:
        for j in i["acc"]:
            acc_y.append(j[1])

    acc_z = []
    for i in all_data:
        for j in i["acc"]:
            acc_z.append(j[2])
    acc_x = np.array(acc_x)
    acc_y = np.array(acc_y)
    acc_z = np.array(acc_z)

    # preprocess HR
    hr_x = np.array([np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data])
    hr_y = [i["hr"] for i in all_data]

    if len(all_data) == 0:
        print("no data")
        sys.exit(0)
    if len(all_data[0]["ecg"]) != ECG_HZ:
        print("wrong ECG_HZ value")
        sys.exit(0)

    lead_off_count = 0
    lead_off_time = []
    for i in all_data:
        if i["leadOn"] != 1:
            lead_off_count += 1
            time = np.datetime64(i["recordTime"], "ms") + TIME_ZONE
            lead_off_time.append(time)

    print(f"lead off count = {lead_off_count}")
    flash_count = 0
    for i in all_data:
        if i["flash"] == 1:
            flash_count += 1
    print(f"flash% = {int(flash_count * 100 / len(all_data))}%")

    if ENABLE_ECG_ACC:
        raw_ecg_x = [np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data]
        raw_ecg_y = [i["ecg"] for i in all_data]
        rwl_x = []
        rwl_y = []
        ecg_x = []
        ecg_y = []
        for i in range(len(raw_ecg_x)):
            if len(raw_ecg_y[i]) != ECG_HZ:
                print("wrong ECG length found, padding with zero")
                raw_ecg_y[i] = [0] * ECG_HZ

            for j in range(ECG_HZ):
                raw_x = raw_ecg_x[i] + np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                raw_y = raw_ecg_y[i][j]
                ecg_x.append(raw_x)
                ecg_y.append(raw_y)
        for i in all_data:
            for j in i["rwl"]:
                if 0 <= j < ECG_HZ:
                    time = np.datetime64(i["recordTime"], "ms") + TIME_ZONE
                    time += np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                    rwl_x.append(time)
                    if len(i["ecg"]) != ECG_HZ:
                        pass
                    else:
                        rwl_y.append(i["ecg"][j])
                else:
                    break

    else:
        all_rri = []
        for i in all_data:
            all_rri += [j for j in i["rri"] if 0 < j < 3000]

        activity_feature = []
        x_activity_feature = []
        for index in range(int(len(acc_x) / ACTIVITY_WINDOW)):
            feature = extract_feature_python(acc_x[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW],
                                         acc_y[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW],
                                         acc_z[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW], ACTIVITY_WINDOW)
            activity_feature.append(feature * ACTIVITY_SCALE)
            index = int(index * (ACTIVITY_WINDOW / ACC_HZ))
            x_activity_feature.append(hr_x[np.clip(index, 0, len(hr_x) - 1)])

    if ENABLE_ECG_ACC:
        ax = plt.subplot(211)
        plt.title("HR")
        plt.ylim(-10, 180)
        ax.set_yticks(np.arange(0, 180, 20))
        plt.grid()
        plt.plot(hr_x, hr_y)
        plt.axhline(80, linestyle="--", color="red")
        plt.axhline(120, linestyle="--", color="red")
        plt.axhline(160, linestyle="--", color="red")

        ax2 = plt.subplot(212, sharex=ax)

        plt.ylim(-5000, 5000)

        new_ecg_y = np.array(ecg_y)
        if False:
            plt.title("Filtered ECG")
            new_ecg_y = remove_baseline_wander(ecg_y)
            new_ecg_y = remove_power(new_ecg_y)
            plt.plot(ecg_x, new_ecg_y)
        else:
            plt.title("Raw ECG")
            magnification = 1000
            if ECG_HZ == 250:
                magnification = 3776
            formatter = ticker.FuncFormatter(lambda x, y: f"{x / magnification:.3}mV")
            ax2.yaxis.set_major_formatter(formatter)

            plt.plot(ecg_x, new_ecg_y)
            plt.scatter(rwl_x, rwl_y, color="red", marker="x")
            plt.scatter(lead_off_time, [0] * len(lead_off_time), color="red", marker="o")

        for i in missing_tick:
            begin = np.datetime64(i[0], "ms") + TIME_ZONE
            end = np.datetime64(i[1], "ms") + TIME_ZONE
            plt.axvspan(begin, end, facecolor='red', alpha=0.5)

        color = "red"
        ax22 = ax2.twinx()
        ax22.set_ylabel('acc', color=color)
        ax22.tick_params(axis='y', labelcolor=color)

        ax22.plot(acc_time, acc_x, label="ACC(x)")
        ax22.plot(acc_time, acc_y, label="ACC(y)")
        ax22.plot(acc_time, acc_z, label="ACC(z)")
        ax22.set_ylim(-4096, 14000)
        plt.legend()
        plt.show()


    else:
        plt.ylim(-10, 160)
        plt.plot(hr_x, hr_y)
        plt.axhline(80, linestyle="--", label="80")
        # sdnn, rmssd, stress = gen_hrv(all_rri, SDNN_DURATION)
        # plt.plot(hr_x[[SDNN_DURATION * i for i in range(len(sdnn))]], stress)
        plt.scatter(x_activity_feature, activity_feature, color='purple')
        nl.poincare(all_rri)
        fd.welch_psd(all_rri)


