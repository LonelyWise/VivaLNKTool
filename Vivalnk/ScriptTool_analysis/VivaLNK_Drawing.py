#!/usr/bin/env python 
# coding:utf-8
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
plt.rcParams['agg.path.chunksize'] = 10000
from matplotlib import ticker
import numpy as np
import sys
# import pyhrv
# import pyhrv.tools as tools
# import pyhrv.frequency_domain as fd
# import pyhrv.nonlinear as nl
# import pyhrv.time_domain as td
from scipy.signal import butter, filtfilt
import time

'''
用于绘制各种数据的波形
ECG、Temp、Spo2、BP

ECG可以支持多种组合参数去绘制

支持ECG、HR和RR的对比绘图
'''

TIME_ZONE = np.timedelta64(8, "h")
ECG_HZ = 128
ENABLE_ECG_ACC = True
SDNN_DURATION = 300
ACTIVITY_WINDOW = 5 * 10  # 10 seconds
ACC_HZ = 5
ACTIVITY_SCALE = 50

class DrawingView:
    def __init__(self, write_path, Draw_log):
        self.write_path = write_path
        self.Draw_log = Draw_log
        self.denoise_waveform = False
        self.draw_parameter = None
        self.file_name1 = ""
        self.file_name2 = ""

    def draw_waveform(self, all_data, missing_tick):
        '''
        绘制波形
        ecg acc HR 和RR
        '''
        if len(all_data) == 0:
            self.Draw_log("no data")
            sys.exit(0)
        # 获取绘制哪些参数波形的值
        draw_hr_value = self.draw_parameter['hr']
        draw_ecg_value = self.draw_parameter['ecg']
        draw_acc_value = self.draw_parameter['acc']
        draw_rr_value = self.draw_parameter['rr']
        draw_rwl_value = self.draw_parameter['rwl']
        draw_count = 0
        if draw_hr_value:
            draw_count += 1
        if draw_rr_value:
            draw_count += 1
        if draw_ecg_value or draw_acc_value:
            draw_count += 1
        record_wave_count = 0
        record_rr = False
        # 只有acc和rr时 应该是查看呼吸率和acc的关系  使用只有这两个的绘图
        if draw_acc_value==True and draw_rr_value == True and draw_hr_value==False and draw_ecg_value==False:
            self.draw_acc(all_data)
            return

        # preprocess ACC
        acc_time = []
        acc_x = []
        acc_y = []
        acc_z = []
        hr_y = []
        rr_y = []

        lead_off_count = 0
        lead_off_time = []
        flash_count = 0

        for index in range(len(all_data)):
            i = all_data[index]
            if len(i['ecg']) != ECG_HZ:
                self.Draw_log("wrong ECG_HZ value")
                sys.exit(0)

            acc_hz = len(i["acc"])
            acc_cycle = 1000 / acc_hz
            if 'HR' in i.keys():
                hr_y.append(i['HR'])
            elif 'hr' in i.keys():
                hr_y.append(i['hr'])

            if 'RR' in i.keys():
                rr_y.append(i['RR'])
            elif 'rr' in i.keys():
                rr_y.append(i['rr'])

            if i["leadOn"] != 1:
                lead_off_count += 1
                record_ct_time = np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE
                lead_off_time.append(record_ct_time)

            if i["flash"] == 1:
                flash_count += 1

            for index2 in range(acc_hz):
                j = i["acc"][index2]
                if type(j) is dict:
                    acc_x.append(j['x'])
                    acc_y.append(j['y'])
                    acc_z.append(j['z'])
                    acc_time.append(np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2), "ms"))
                elif type(j) is list:
                    acc_x.append(j[0])
                    acc_y.append(j[1])
                    acc_z.append(j[2])
                    acc_time.append(np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2), "ms"))

        acc_x = np.array(acc_x)
        acc_y = np.array(acc_y)
        acc_z = np.array(acc_z)

        # 获取心率横轴的时间数组
        hr_x_time = np.array([np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in all_data])

        self.Draw_log(f"lead off count = {lead_off_count}")
        self.Draw_log(f"flash% = {int(flash_count * 100 / len(all_data))}%")

        # hrv分析
        # self.analysis_hrv(all_data)

        raw_ecg_x = [np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in all_data]
        raw_ecg_y = [i["ecg"] for i in all_data]
        rwl_x = []
        rwl_y = []
        ecg_x = []
        ecg_y = []
        for i in range(len(raw_ecg_x)):
            if len(raw_ecg_y[i]) != ECG_HZ:
                self.Draw_log(f"wrong ECG length found, padding with zero")
                raw_ecg_y[i] = [0] * ECG_HZ

            for j in range(ECG_HZ):
                raw_x = raw_ecg_x[i] + np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                raw_y = raw_ecg_y[i][j]
                ecg_x.append(raw_x)
                ecg_y.append(int(raw_y))

        if draw_rwl_value:
            for i in all_data:
                for j in i["rwl"]:
                    if 0 <= j < ECG_HZ:
                        time = np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE
                        time += np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                        rwl_x.append(time)
                        if len(i["ecg"]) != ECG_HZ:
                            pass
                        else:
                            rwl_y.append(i["ecg"][j])
                    else:
                        break

        plt.figure()
        if draw_hr_value:
            record_wave_count += 1
            self.hr_ax = plt.subplot(draw_count, 1, record_wave_count)
            plt.title("HR")
            plt.ylim(-10, 180)
            self.hr_ax.set_yticks(np.arange(0, 180, 20))
            plt.grid()
            plt.plot(hr_x_time, hr_y)
            plt.axhline(80, linestyle="--", color="red")
            plt.axhline(120, linestyle="--", color="red")
            plt.axhline(160, linestyle="--", color="red")

        if draw_rr_value:
            record_rr = True
            record_wave_count += 1
            if record_wave_count == 1:
                self.rr_x = plt.subplot(draw_count, 1, 1)
            else:
                self.rr_x = plt.subplot(draw_count, 1, 2, sharex=self.hr_ax)
            plt.title('RR')
            plt.ylim(0,70)
            plt.plot(hr_x_time,rr_y)

        if draw_ecg_value:
            record_wave_count += 1
            if record_wave_count == 1:
                self.ecg_ax = plt.subplot(draw_count, 1, 1)
            elif record_wave_count == 2:
                if record_rr:
                    self.ecg_ax = plt.subplot(draw_count, 1, 2, sharex=self.rr_x)
                else:
                    self.ecg_ax = plt.subplot(draw_count, 1, 2, sharex=self.hr_ax)
            elif record_wave_count == 3:
                self.ecg_ax = plt.subplot(draw_count, 1, 3, sharex=self.rr_x)

            plt.ylim(-5000, 5000)
            new_ecg_y = np.array(ecg_y)

            plt.title("Raw ECG")
            magnification = 1000
            if ECG_HZ == 250:
                magnification = 3776
            formatter = ticker.FuncFormatter(lambda x, y: f"{x / magnification:.3}mV")
            self.ecg_ax.yaxis.set_major_formatter(formatter)

            if self.denoise_waveform:
                new_ecg_y = self.remove_baseline_wander(new_ecg_y)

            plt.plot(ecg_x, new_ecg_y)

            # plt.axhline(y=0.4, linestyle="--", color="red")
            # plt.axhline(y=0.6, linestyle="--", color="red")
            # plt.axhline(y=0.8, linestyle="--", color="red")

            # for i in range(0,len(rwl_x)-1):
            #     plt.axvline(x=rwl_x[i], color="red", linestyle='--',label = str(rwl_x[i]))

            # location_text = []
            # for rwl_location in rwl_x:
            #     index_p = ecg_x.index(rwl_location)
            #     location_text.append(index_p)

            # print(location_text)
            # print(rwl_y)
            # print(rwl_x)
            if draw_rwl_value:
                plt.scatter(rwl_x, rwl_y, color="red", marker="x")
            # for n in range(0,len(location_text)):
            #     print(f'x = {location_text[n]}   y={rwl_y[n]}')
            #     # plt.text(location_text[i], rwl_y[i], str(rwl_y[i]), family='serif', style='italic', ha='right', wrap=True)
            #     plt.annotate("123", xy=(location_text[n], rwl_y[n]), xytext=(-20, 10),textcoords='offset points')

            # 有lead off时才需要绘制
            if len(lead_off_time) != 0:
                plt.scatter(lead_off_time, [0] * len(lead_off_time), color="red", marker="o")

            for i in missing_tick:
                begin = np.datetime64(i[0], "ms") + TIME_ZONE
                end = np.datetime64(i[1], "ms") + TIME_ZONE
                plt.axvspan(begin, end, facecolor='red', alpha=0.5)

        if draw_acc_value:
            record_wave_count += 1
            if draw_ecg_value == False:
                if record_wave_count == 1:
                    self.acc_ax = plt.subplot(draw_count, 1, 1)
                elif record_wave_count == 2:
                    if record_rr:
                        self.acc_ax = plt.subplot(draw_count, 1, 2, sharex=self.rr_x)
                    else:
                        self.acc_ax = plt.subplot(draw_count, 1, 2, sharex=self.hr_ax)
                else:
                    self.acc_ax = plt.subplot(draw_count, 1, 3, sharex=self.rr_x)

                self.acc_ax.set_ylabel('acc', color="red")
                self.acc_ax.tick_params(axis='y', labelcolor="red")

                self.acc_ax.plot(acc_time, acc_x, label="ACC(x)")
                self.acc_ax.plot(acc_time, acc_y, label="ACC(y)")
                self.acc_ax.plot(acc_time, acc_z, label="ACC(z)")
                self.acc_ax.set_ylim(-4096, 4096)
            else:
                ax22 = self.ecg_ax.twinx()
                ax22.set_ylabel('acc', color="red")
                ax22.tick_params(axis='y', labelcolor="red")

                ax22.plot(acc_time, acc_x, label="ACC(x)")
                ax22.plot(acc_time, acc_y, label="ACC(y)")
                ax22.plot(acc_time, acc_z, label="ACC(z)")
                ax22.set_ylim(-4096, 4096)
        plt.legend()
        plt.show()

    def draw_mit_ishne(self, all_data):
        raw_ecg_x = [np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data]
        raw_ecg_y = [i["ecg"] for i in all_data]
        ecg_x = []
        ecg_y = []
        for i in range(len(raw_ecg_x)):
            if len(raw_ecg_y[i]) != ECG_HZ:
                self.Draw_log(f"wrong ECG length found, padding with zero")
                raw_ecg_y[i] = [0] * ECG_HZ

            for j in range(ECG_HZ):
                raw_x = raw_ecg_x[i] + np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                raw_y = raw_ecg_y[i][j]
                ecg_x.append(raw_x)
                ecg_y.append(raw_y)

        ax2 = plt.subplot(111)

        plt.ylim(-5000, 5000)

        new_ecg_y = np.array(ecg_y)

        plt.title("Raw ECG")
        magnification = 1000
        if ECG_HZ == 250:
            magnification = 3776
        formatter = ticker.FuncFormatter(lambda x, y: f"{x / magnification:.3}mV")
        ax2.yaxis.set_major_formatter(formatter)

        if self.denoise_waveform:
            new_ecg_y = self.remove_baseline_wander(new_ecg_y)

        plt.plot(ecg_x, new_ecg_y)

        plt.legend()
        plt.show()

    def remove_baseline_wander(self, y):
        fs = ECG_HZ
        high_pass = 1.28  # hz
        nyq = 0.5 * fs
        high = high_pass / nyq

        b, a = butter(2, high, 'high')
        return filtfilt(b, a, y)

    def draw_temp(self, temp_data):
        """
        原始温度和算法温度分开绘制
        实时和历史分开绘制
        电量只绘制实时数据的
        """
        temp_realtime_x = []
        temp_flash_x = []
        temp_realtime_data_raw = []
        temp_flash_data_raw = []
        temp_realtime_data_display = []
        temp_flash_data_display = []
        battery_data = []
        for temp_dict in temp_data:
            flash = temp_dict['flash']
            if flash is False:
                temp_realtime_x.append(np.datetime64(int(temp_dict["recordTime"]), "ms") + np.timedelta64(8, "h"))
                battery_data.append(temp_dict['battery'])
                if 'raw' in temp_dict:
                    temp_realtime_data_raw.append(float(temp_dict['raw']))
                    temp_realtime_data_display.append(float(temp_dict['display']))
                elif 'rawTemp' in temp_dict:
                    temp_realtime_data_raw.append(float(temp_dict['rawTemp']))
                    temp_realtime_data_display.append(float(temp_dict['displayTemp']))
            else:
                temp_flash_x.append(np.datetime64(int(temp_dict["recordTime"]), "ms") + np.timedelta64(8, "h"))
                if 'raw' in temp_dict:
                    temp_flash_data_raw.append(float(temp_dict['raw']))
                    temp_flash_data_display.append(float(temp_dict['display']))
                elif 'rawTemp' in temp_dict:
                    temp_flash_data_raw.append(float(temp_dict['rawTemp']))
                    temp_flash_data_display.append(float(temp_dict['displayTemp']))

        raw_ax = plt.subplot(311)
        plt.title("raw temperature Wave")
        raw_ax.set_yticks(np.arange(20, 40, 2))
        formatter = ticker.FuncFormatter(lambda x, y: f"{x}℃")
        raw_ax.yaxis.set_major_formatter(formatter)
        raw_ax.plot(temp_realtime_x, temp_realtime_data_raw, 'o-', markersize=3, label='realtime raw')
        if len(temp_flash_data_raw) != 0:
            raw_ax.plot(temp_flash_x, temp_flash_data_raw, 'o-', markersize=3, label='flash raw')
        raw_ax.axhline(35.5, linestyle="--", color="red")
        raw_ax.axhline(37.5, linestyle="--", color="red")
        plt.ylim(20, 40)
        plt.legend()

        display_ax = plt.subplot(312, sharex=raw_ax)
        plt.title("display temperature Wave")
        display_ax.set_yticks(np.arange(20, 40, 2))
        formatter = ticker.FuncFormatter(lambda x, y: f"{x}℃")
        display_ax.yaxis.set_major_formatter(formatter)
        display_ax.plot(temp_realtime_x, temp_realtime_data_display, 'o-', markersize=3, label='realtime display')
        if len(temp_flash_data_display) != 0:
            display_ax.plot(temp_flash_x, temp_flash_data_display, 'o-', markersize=3, label='flash display')
        display_ax.axhline(35.5, linestyle="--", color="red")
        display_ax.axhline(37.5, linestyle="--", color="red")
        plt.ylim(20, 40)
        plt.legend()

        ax2 = plt.subplot(313, sharex=display_ax)
        ax2.set_yticks(np.arange(-10, 105, 10))
        ax2.plot(temp_realtime_x, battery_data, label="battery")
        plt.ylim(-10, 105)

        plt.legend()  # 显示左下角的图例
        plt.show()

    def draw_SpO2(self, spo2_data):
        """
        历史和实时数据波形分开绘制
        """
        spo2_realtime_data = []
        spo2_flash_data = []
        spo2_realtime_x = []
        spo2_flash_x = []

        pi_y = []
        pi_time = []

        spo2_wave_y = []
        spo2_wave_time = []
        for spo2_dict in spo2_data:
            flash = spo2_dict['flash']
            if flash is False:
                spo2_realtime_x.append(np.datetime64(int(spo2_dict["recordTime"]), "ms") + TIME_ZONE)
                spo2_realtime_data.append(spo2_dict['spo2'])
            else:
                spo2_flash_x.append(np.datetime64(int(spo2_dict["recordTime"]), "ms") + TIME_ZONE)
                spo2_flash_data.append(spo2_dict['spo2'])

            if "pi" in spo2_dict:
                pi_y.append(spo2_dict["pi"])
                pi_time.append(np.datetime64(int(spo2_dict["recordTime"]), "ms") + TIME_ZONE)

            if "waveform" in spo2_dict:
                spo2_wave = spo2_dict['waveform']
                if len(spo2_wave) == 0:
                    continue
                spo2_cycle = 1000 / len(spo2_wave)
                for index in range(len(spo2_wave)):
                    spo2_wave_y.append(spo2_wave[index])
                    time_point = np.datetime64(spo2_dict['recordTime'], "ms") + TIME_ZONE + np.timedelta64(int(spo2_cycle * index),"ms")
                    spo2_wave_time.append(time_point)

        draw_count = 1
        if len(spo2_wave_y) != 0:
            draw_count += 1
        if len(pi_y) != 0:
            draw_count += 1

        record_draw_count = 1

        ax = plt.subplot(draw_count, 1, 1)
        ax.set_ylabel('SpO2')
        plt.title("SpO2 Wave")
        plt.ylim(80, 100)
        ax.set_yticks(np.arange(80, 100, 5))
        # plt.grid()
        if len(spo2_realtime_data) != 0:
            plt.plot(spo2_realtime_x, spo2_realtime_data, 'o-', markersize=3, label='RealTime SpO2')
        if len(spo2_flash_data) != 0:
            plt.plot(spo2_flash_x, spo2_flash_data, 'o-', markersize=3, label='Flash Spo2')
        plt.axhline(90, linestyle="--", color="red")
        plt.axhline(95, linestyle="--", color="red")
        plt.legend()

        if len(spo2_wave_y) != 0:
            record_draw_count += 1
            ax2 = plt.subplot(draw_count, 1, record_draw_count, sharex=ax)
            ax2.plot(spo2_wave_time, spo2_wave_y, label="waveform")
            plt.legend()
            if len(pi_y) != 0:
                record_draw_count += 1
                ax_pi = plt.subplot(draw_count, 1, record_draw_count, sharex=ax2)
                ax_pi.set_yticks(np.arange(-2, 11, 1))
                plt.ylim(-1, 10)
                plt.plot(pi_time, pi_y, 'o-', markersize=3, label='pi')
                plt.legend()
        else:
            if len(pi_y) != 0:
                record_draw_count += 1
                ax_pi = plt.subplot(draw_count, 1, record_draw_count, sharex=ax)
                ax_pi.set_yticks(np.arange(-2, 11, 1))
                plt.ylim(-1, 10)
                plt.plot(pi_time, pi_y, 'o-', markersize=3, label='pi')
                plt.legend()
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
        ax22.plot(bp_x, dia_y, 'o-',label="Dia",color='red')

        ax22.set_ylim(50, 100)
        plt.legend()  # 显示左下角的图例

        plt.show()

    def draw_acc(self, all_data):
        acc_x = []
        acc_y = []
        acc_z = []
        acc_time = []
        rr_y = []
        rr_x = np.array([np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in all_data])
        rr_min = 0
        rr_max = 0

        acc_x_min = 0
        acc_x_max = 0

        acc_y_min = 0
        acc_y_max = 0

        acc_z_min = 0
        acc_z_max = 0

        for index in range(len(all_data)):
            i = all_data[index]
            acc_hz = len(i["acc"])
            acc_cycle = 1000 / acc_hz

            rr_value = 0
            if 'RR' in i.keys():
                rr_value = i['RR']
            elif 'rr' in i.keys():
                rr_value = i['rr']
            rr_y.append(rr_value)
            if rr_min == 0:
                rr_min = rr_value
            if rr_max == 0:
                rr_max = rr_value

            if rr_min > rr_value:
                rr_min = rr_value
            if rr_max < rr_value:
                rr_max = rr_value

            for index2 in range(acc_hz):
                j_tuple = i["acc"][index2]
                # print(isinstance(j_tuple,list))
                if isinstance(j_tuple,dict):
                    acc_x.append(j_tuple['x'])
                    acc_y.append(j_tuple['y'])
                    acc_z.append(j_tuple['z'])
                    acc_time.append(
                        np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2),
                                                                                               "ms"))
                elif isinstance(j_tuple,list):
                    if acc_x_min == 0 and acc_x_max == 0:
                        acc_x_min = j_tuple[0]
                        acc_x_max = j_tuple[0]

                    if acc_y_min == 0 and acc_y_max == 0:
                        acc_y_min = j_tuple[1]
                        acc_y_max = j_tuple[1]

                    if acc_z_min == 0 and acc_z_max == 0:
                        acc_z_min = j_tuple[2]
                        acc_z_max = j_tuple[2]

                    if acc_x_min > j_tuple[0]:
                        acc_x_min = j_tuple[0]
                    if acc_x_max < j_tuple[0]:
                        acc_x_max = j_tuple[0]

                    if acc_y_min > j_tuple[1]:
                        acc_y_min = j_tuple[1]
                    if acc_y_max < j_tuple[1]:
                        acc_y_max = j_tuple[1]

                    if acc_z_min > j_tuple[2]:
                        acc_z_min = j_tuple[2]
                    if acc_z_max < j_tuple[2]:
                        acc_z_max = j_tuple[2]

                    acc_x.append(j_tuple[0])
                    acc_y.append(j_tuple[1])
                    acc_z.append(j_tuple[2])
                    acc_time.append(
                        np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE + np.timedelta64(int(acc_cycle * index2),
                                                                                               "ms"))
        acc_x = np.array(acc_x)
        acc_y = np.array(acc_y)
        acc_z = np.array(acc_z)

        rr_plt = plt.subplot(411)
        plt.title("RR")
        plt.plot(rr_x, rr_y)
        plt.ylim(rr_min-5, rr_max+5)

        x_plt = plt.subplot(412, sharex=rr_plt)
        plt.title("ACC-X")
        plt.plot(acc_time, acc_x)
        plt.ylim(acc_x_min-20, acc_x_max+20)

        y_plt = plt.subplot(413, sharex=x_plt)
        plt.title("ACC-Y")
        plt.plot(acc_time, acc_y)
        plt.ylim(acc_y_min-20, acc_y_max+20)

        z_plt = plt.subplot(414, sharex=y_plt)
        plt.title("ACC-Z")
        plt.plot(acc_time, acc_z)
        plt.ylim(acc_z_min-20, acc_z_max+20)

        plt.legend
        plt.show()

    def draw_comparison_waveform(self, data1, data2, type):
        if type == 'ecg':
            # 获取绘制哪些参数波形的值
            draw_hr_value = self.draw_parameter['hr']
            draw_ecg_value = self.draw_parameter['ecg']
            draw_rr_value = self.draw_parameter['rr']
            draw_count = 0
            if draw_hr_value:
                draw_count += 1
            if draw_rr_value:
                draw_count += 1
            if draw_ecg_value:
                draw_count += 1
            record_wave_count = 0

            comparison_rr = False
            hr1_array = []
            hr2_array = []
            rr1_arry = []
            rr2_arry = []

            ax1_time = np.array([np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in data1])
            ax2_time = np.array([np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in data2])

            for dict in data1:
                hr1_value = 0
                rr1_value = 0
                if 'hr' in dict:
                    hr1_value = dict['hr']
                if 'rr' in dict:
                    rr1_value = dict['rr']
                hr1_array.append(hr1_value)
                rr1_arry.append(rr1_value)

            for dict in data2:
                hr2_value = 0
                rr2_value = 0
                if 'hr' in dict:
                    hr2_value = dict['hr']
                if 'rr' in dict:
                    rr2_value = dict['rr']
                hr2_array.append(hr2_value)
                rr2_arry.append(rr2_value)

            plt.figure()
            if draw_hr_value:
                record_wave_count += 1
                self.hr_ax = plt.subplot(draw_count,1,record_wave_count)
                plt.plot(ax1_time, hr1_array, label=self.file_name1)
                plt.plot(ax2_time, hr2_array, label=self.file_name2)
                plt.legend()

            if draw_rr_value:
                comparison_rr = True
                record_wave_count += 1
                if record_wave_count == 1:
                    self.rr_ax = plt.subplot(draw_count, 1, 1)
                else:
                    self.rr_ax = plt.subplot(draw_count, 1, 2, sharex=self.hr_ax)

                rr1_mean = np.mean(rr1_arry)
                rr2_mean = np.mean(rr2_arry)
                print(f"均值：rr1:{rr1_mean}    rr2:{rr2_mean}")
                rr1_var = np.var(rr1_arry)
                rr2_var = np.var(rr2_arry)
                print(f"方差：rr1:{rr1_var}    rr2:{rr2_var}")
                rr1_stand = np.sqrt(np.var(rr1_arry))
                rr2_stand = np.sqrt(np.var(rr2_arry))

                rr_title1 = self.file_name1 + f"\nmean={'%.2f' % rr1_mean}\nvariance={'%.2f' % rr1_var}\nstandard deviation={'%.2f' % rr1_stand}"
                rr_title2 = self.file_name2 + f"\nmean={'%.2f' % rr2_mean}\nvariance={'%.2f' % rr2_var}\nstandard deviation={'%.2f' % rr2_stand}"
                plt.plot(ax1_time, rr1_arry, label=rr_title1)
                plt.plot(ax2_time, rr2_arry, label=rr_title2)
                plt.legend()

            if draw_ecg_value:
                record_wave_count += 1
                raw_ecg_x1 = [np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in data1]
                raw_ecg_y1 = [i["ecg"] for i in data1]

                ecg_ax_time1 = []
                ecg1_array = []

                for i in range(len(raw_ecg_x1)):
                    for j in range(ECG_HZ):
                        raw_x = raw_ecg_x1[i] + np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                        ecg_ax_time1.append(raw_x)
                        raw_y = raw_ecg_y1[i][j]
                        ecg1_array.append(int(raw_y))

                raw_ecg_x2 = [np.datetime64(int(i["recordTime"]), "ms") + TIME_ZONE for i in data2]
                raw_ecg_y2 = [i["ecg"] for i in data2]

                ecg_ax_time2 = []
                ecg2_array = []

                for i in range(len(raw_ecg_x2)):
                    for j in range(ECG_HZ):
                        raw_x = raw_ecg_x2[i] + np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
                        ecg_ax_time2.append(raw_x)
                        raw_y = raw_ecg_y2[i][j]
                        ecg2_array.append(int(raw_y))

                if record_wave_count == 1:
                    plt.subplot(draw_count,1,record_wave_count)
                elif record_wave_count == 2:
                    if comparison_rr:
                        plt.subplot(draw_count,1,record_wave_count,sharex=self.rr_ax)
                    else:
                        plt.subplot(draw_count,1,record_wave_count,sharex=self.hr_ax)
                elif record_wave_count == 3:
                    plt.subplot(draw_count,1,record_wave_count,sharex=self.rr_ax)

                plt.plot(ecg_ax_time1,ecg1_array,label=self.file_name1)
                plt.plot(ecg_ax_time2,ecg2_array,label=self.file_name2)
                plt.legend()
            plt.show()

    # def analysis_hrv(self,all_data):
    #     if 'rri' not in all_data[0].keys():
    #         return
    #     total_rri = []
    #     for i in all_data:
    #         total_rri += [j for j in i["rri"] if 0 < j < 3000]
    #     self.time_domain_report(total_rri)
    #     if self.write_path != '':
    #         self.write_path = self.write_path + '/'
    #         print(self.write_path)
    #         result = pyhrv.hrv(total_rri)
    #         tools.hrv_export(results=result,path=self.write_path)

    # def time_domain_report(self,nni):
    #
    #     # Time Domain results
    #     print("=========================")
    #     print("TIME DOMAIN Results")
    #     print("=========================")
    #
    #     hr_ = td.hr_parameters(nni)
    #     print("HR Results")
    #     print("> Mean HR:			%f [bpm]" % hr_['hr_mean'])
    #     print("> Min HR:			%f [bpm]" % hr_['hr_min'])
    #     print("> Max HR:			%f [bpm]" % hr_['hr_max'])
    #     print("> Std. Dev. HR:		%f [bpm]" % hr_['hr_std'])
    #
    #     nni_para_ = td.nni_parameters(nni)
    #     print("NN Results")
    #     print("> Mean NN:			%f [ms]" % nni_para_['nni_mean'])
    #     print("> Min NN:			%f [ms]" % nni_para_['nni_min'])
    #     print("> Max NN:			%f [ms]" % nni_para_['nni_max'])
    #
    #     nni_diff_ = td.nni_differences_parameters(nni)
    #     print("∆NN Results")
    #     print("> Mean ∆NN:			%f [ms]" % nni_diff_['nni_diff_mean'])
    #     print("> Min ∆NN:			%f [ms]" % nni_diff_['nni_diff_min'])
    #     print("> Max ∆NN:			%f [ms]" % nni_diff_['nni_diff_max'])
    #
    #     print("SDNN:				%f [ms]" % td.sdnn(nni)['sdnn'])
    #     print("SDNN Index:			%f [ms]" % td.sdnn_index(nni)['sdnn_index'])
    #     print("SDANN:				%f [ms]" % td.sdann(nni)['sdann'])
    #     print("RMMSD:				%f [ms]" % td.rmssd(nni)['rmssd'])
    #     print("SDSD:				%f [ms]" % td.sdsd(nni)['sdsd'])
    #     print("NN50:				%i [-]" % td.nn50(nni)['nn50'])
    #     print("pNN50: 				%f [%%]" % td.nn50(nni)['pnn50'])
    #     print("NN20:				%i [-]" % td.nn20(nni)['nn20'])
    #     print("pNN20: 				%f [%%]" % td.nn20(nni)['pnn20'])

    # def extract_feature_python(self, x, y, z, width=50, Wn=[0.1, 0.9]):
    #     # Center each axis and calculate the total acceleration.
    #     total = np.sqrt((x - np.mean(x)) ** 2 + (y - np.mean(y)) ** 2 + (z - np.mean(z)) ** 2)
    #     # Filter the total acceleration.
    #     b, a = butter(2, Wn, btype="bandpass")
    #     total = filtfilt(b, a, total)
    #     feature = np.std(total)
    #     if feature > 1000:
    #         return 4
    #     elif feature > 400:
    #         return 3
    #     elif feature > 65:
    #         return 2
    #     elif feature > 0:
    #         return


def print_msg(msg):
    print(msg)
if __name__ == "__main__":
    from VivaLNK_Reading import ReadFile

    read_file = ReadFile(print_msg)
    # all_data,miss,type = read_file.read_batch_files_data(["/Users/weixu/Documents/维灵/数据分析/呼吸率相关/只使用ACC/VVRealDataLog 2021-10-27 09-56.log"],-1)
    all_data,miss,type = read_file.read_batch_files_data(["/Users/weixu/Documents/维灵/数据分析/呼吸率相关/只使用ACC/ailin-10hz.log"],-1)
    draw_acc = DrawingView('',print_msg)
    draw_acc.draw_acc(all_data)