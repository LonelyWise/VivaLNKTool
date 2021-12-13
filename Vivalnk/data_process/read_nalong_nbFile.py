#!/usr/bin/env python 
# coding:utf-8

import codecs
from ScriptTool_analysis.VivaLNK_Drawing import DrawingView
from ScriptTool_analysis.VivaLNK_Reading import ReadFile
from datetime import datetime
from datetime import time
import wfdb
import os
import numpy as np


class NalongDataAnalysis:
    def __init__(self,dir_path,nalong_log,mit_start_time):
        self.dir_path = dir_path
        self.nalong_log = nalong_log
        self.mit_start_time = mit_start_time
        self.nalong_log('纳龙NB格式数据解析')

    def read_nb_file_content(self,file_name):
        ecg_data = []
        data = codecs.open(file_name, encoding="UTF-8")
        lines = data.readlines()

        for every_line in lines:
            every_line = every_line.replace('\n', '')
            every_line = every_line.replace(' ', '')
            for i in range(1, len(every_line) + 1):
                if i % 2 == 0:
                    value1 = self.getValue(every_line[i - 2])
                    value2 = self.getValue(every_line[i - 1])

                    value = value1 * 16 + value2
                    ecg_data.append(value)

        data.close()
        self.nalong_log('nb文件解析完成')

        ecg_data = ecg_data[12:]

        big_ecg_array = []
        real_ecg = []
        count = 0
        for i in range(1, len(ecg_data) + 1):
            if i % 2 == 0:
                count += 1
                ecg_value = ecg_data[i - 2] + ecg_data[i - 1] * 16 * 16
                if ecg_value > 32768:
                    ecg_value = (65535 - ecg_value + 1) * -1

                real_ecg.append(ecg_value)

        self.nalong_log('ecg数据解析完成')
        ecg_data = []

        ecg_all = []
        ecg_all.append(real_ecg)
        # 生成mit16的文件
        self.generate_mit_file('nalong'+'-'+str(self.mit_start_time), 128, [1000], ecg_all, self.mit_start_time, None, self.dir_path + 'mit16/')

    def generate_mit_file(self,record_name, sample_frequency, amplitudes, ecg_list, start_record_mills, tzinfo, output_dir_path):
        if not ecg_list or len(ecg_list) == 0:
            return []
        channels = len(ecg_list)
        units = ['mV'] * channels
        signal_name = ['I'] * channels
        adc_gains = amplitudes
        formats = ['16'] * channels
        baselines = [0] * channels
        digital_signals = []
        for index in range(len(ecg_list[0])):
            arr = []
            for channel_index in range(channels):
                arr.append(ecg_list[channel_index][index])
            digital_signals.append(arr)
        if len(digital_signals) > 0:
            base_datetime = datetime.fromtimestamp(start_record_mills / 1000).replace(tzinfo=tzinfo)
            base_date = base_datetime.date()
            base_time = base_datetime.time()
            base_time = time(base_time.hour, base_time.minute, base_time.second)
            wfdb.wrsamp(record_name, sample_frequency, units, signal_name, d_signal=np.array(digital_signals),
                        fmt=formats, adc_gain=adc_gains, baseline=baselines, base_date=base_date, base_time=base_time,
                        write_dir=output_dir_path)
            header_file_path = os.path.join(output_dir_path, record_name + '.hea')
            data_file_path = os.path.join(output_dir_path, record_name + '.dat')
            self.nalong_log('mit16文件生成 '+ header_file_path + ' ' + data_file_path)

            self.analysis_mit16_file(header_file_path)

    def analysis_mit16_file(self, file_path_name):
        read_file = ReadFile(ReadFile_log=self.nalong_log)
        all_data = read_file.read_mit16_data(file_path_name)
        drawing_view = DrawingView('', Draw_log=self.nalong_log)
        drawing_view.draw_ECG_acc(all_data, [])

    def getValue(self,line_str):
        if line_str == 'a':
            return 10
        elif line_str == 'b':
            return 11
        elif line_str == 'c':
            return 12
        elif line_str == 'd':
            return 13
        elif line_str == 'e':
            return 14
        elif line_str == 'f':
            return 15
        else:
            return int(line_str)

        return 0

