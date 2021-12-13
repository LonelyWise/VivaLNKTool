#!/usr/bin/env python 
# coding:utf-8
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
import sys
from scipy.signal import butter, filtfilt


TIME_ZONE = np.timedelta64(8, "h")
ECG_HZ = 128
ENABLE_ECG_ACC = True
SDNN_DURATION = 300
ACTIVITY_WINDOW = 5 * 10  # 10 seconds
ACC_HZ = 5
ACTIVITY_SCALE = 50

class DrawingView:
    def __init__(self,write_path):
        self.write_path = write_path
        print('开始绘制')

    def draw_ECG_acc(self, all_data, missing_tick):
        # preprocess ACC
        acc_time = []
        acc_x = []
        acc_y = []
        acc_z = []
        hr_y = []
        for index in range(len(all_data)):
            i = all_data[index]
            acc_hz = len(i["acc"])
            acc_cycle = 1000 / acc_hz
            if 'HR' in i.keys():
                hr_y.append(i['HR'])
            elif 'hr' in i.keys():
                hr_y.append(i['hr'])

            for index2 in range(acc_hz):
                j = i["acc"][index2]
                if type(j) is dict:
                    acc_x.append(j['x'])
                    acc_y.append(j['y'])
                    acc_z.append(j['z'])
                    acc_time.append(np.datetime64(i["recordTime"], "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2), "ms"))
                elif type(j) is list:
                    acc_x.append(j[0])
                    acc_y.append(j[1])
                    acc_z.append(j[2])
                    acc_time.append(np.datetime64(i["recordTime"], "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2), "ms"))


        acc_x = np.array(acc_x)
        acc_y = np.array(acc_y)
        acc_z = np.array(acc_z)

        # preprocess HR
        hr_x = np.array([np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data])

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
                    print(f"wrong ECG length found, padding with zero")
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
                feature = self.extract_feature_python(acc_x[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW],
                                                      acc_y[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW],
                                                      acc_z[index * ACTIVITY_WINDOW:(index + 1) * ACTIVITY_WINDOW],
                                                      ACTIVITY_WINDOW)
                activity_feature.append(feature * ACTIVITY_SCALE)
                index = int(index * (ACTIVITY_WINDOW / ACC_HZ))
                x_activity_feature.append(hr_x[np.clip(index, 0, len(hr_x) - 1)])


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
            new_ecg_y = self.remove_baseline_wander(ecg_y)
            new_ecg_y = remove_power(new_ecg_y)
            plt.plot(ecg_x, new_ecg_y)
        else:
            plt.title("Raw ECG")
            magnification = 1000
            if ECG_HZ == 250:
                magnification = 3776
            formatter = ticker.FuncFormatter(lambda x, y: f"{x / magnification:.3}mV")
            ax2.yaxis.set_major_formatter(formatter)

            # new_ecg_y = self.remove_baseline_wander(new_ecg_y)

            plt.plot(ecg_x, new_ecg_y)

            # plt.axhline(y=0.4, linestyle="--", color="red")
            # plt.axhline(y=0.6, linestyle="--", color="red")
            # plt.axhline(y=0.8, linestyle="--", color="red")

            # for i in range(0,len(rwl_x)-1):
            #     plt.axvline(x=rwl_x[i], color="red", linestyle='--',label = str(rwl_x[i]))

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


    def extract_feature_python(self, x, y, z, width=50, Wn=[0.1, 0.9]):
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

    def remove_baseline_wander(self, y):
        fs = ECG_HZ
        high_pass = 1.28  # hz
        nyq = 0.5 * fs
        high = high_pass / nyq

        b, a = butter(2, 0.02, 'high')
        return filtfilt(b, a, y)

    def draw_temp(self,temp_data):

        temp_x = np.array([np.datetime64(int(i["recordTime"]), "ms") + np.timedelta64(8, "h") for i in temp_data])
        temp_y = [float(i["displayTemp"]) for i in temp_data]
        battery_y = [i["battery"] for i in temp_data]
        print(temp_y)
        ax = plt.subplot(211)

        plt.title("Temp Wave")
        ax.set_yticks(np.arange(20, 38, 2))
        formatter = ticker.FuncFormatter(lambda x, y: f"{x}℃")
        ax.yaxis.set_major_formatter(formatter)
        # plt.grid()
        ax.plot(temp_x, temp_y, 'o-',label='Temperature')
        ax.axhline(35.5, linestyle="--", color="red")
        ax.axhline(37.5, linestyle="--", color="red")
        plt.ylim(20, 38)

        ax2 = plt.subplot(212, sharex=ax)
        color = "red"
        ax2.set_yticks(np.arange(0, 105, 10))
        ax2.plot(temp_x, battery_y, label="battery")
        plt.ylim(0,105)

        plt.legend()  # 显示左下角的图例
        plt.show()

    def draw_SpO2(self, spo2_data):
        spo2_x = np.array([np.datetime64(int(i["recordTime"]), "ms") + np.timedelta64(8, "h") for i in spo2_data])

        spo2_y = [i["spo2"] for i in spo2_data]
        pi_y = [i["pi"] for i in spo2_data]

        ax = plt.subplot(111)
        ax.set_ylabel('SpO2')
        plt.title("Temp Wave")
        plt.ylim(80, 100)
        ax.set_yticks(np.arange(80, 100, 5))
        # plt.grid()
        plt.plot(spo2_x, spo2_y, 'o-',label='SpO2')
        plt.axhline(90, linestyle="--", color="red")
        plt.axhline(95, linestyle="--", color="red")
        # 右边的y轴
        color = "red"
        ax22 = ax.twinx()
        ax22.set_ylabel('PI', color=color)
        ax22.tick_params(axis='y', labelcolor=color)
        pi_y = np.array(pi_y)
        ax22.plot(spo2_x, pi_y, 'o-',label="PI",color='red')

        ax22.set_ylim(-1, 10)
        plt.legend()  # 显示左下角的图例

        plt.show()

    def draw_BP2(self, bp2_data):
        bp_x = np.array([np.datetime64(int(i["recordTime"]), "ms") + np.timedelta64(8, "h") for i in bp2_data])

        sys_y = [i["sys"] for i in bp2_data]
        dia_y = [i["dia"] for i in bp2_data]

        ax = plt.subplot(111)
        ax.set_ylabel('Sys')
        plt.title("BP Wave")
        plt.ylim(80, 140)
        ax.set_yticks(np.arange(80, 140, 5))
        # plt.grid()
        plt.plot(bp_x, sys_y, 'o-',label='Sys')
        plt.axhline(90, linestyle="--")
        plt.axhline(130, linestyle="--")
        # 右边的y轴
        ax22 = ax.twinx()
        ax22.set_ylabel('Dia')
        ax22.tick_params(axis='y')
        pi_y = np.array(dia_y)
        ax22.plot(bp_x, pi_y, 'o-',label="Dia",color='red')

        ax22.set_ylim(50, 100)
        plt.legend()  # 显示左下角的图例

        plt.show()