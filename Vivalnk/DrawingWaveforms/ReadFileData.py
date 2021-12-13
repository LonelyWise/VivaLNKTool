#!/usr/bin/env python 
# coding:utf-8
import json
import datetime
import time
import wfdb

class ReadFile:
    def __init__(self):
        print('开始读取文件数据')

    def read_file_data(self,read_file_path):
        '''
        :param read_file_path:文件路径
        :return:解析后的所有数据，丢失的数据，类型
        '''
        all_data = []

        with open(read_file_path) as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break

                if lines[0] == '[' and lines[1] == '{':
                    if lines.find('},]') > 0:
                        lines = lines.replace('},]','}]')
                    json_array = json.loads(lines)
                    for jsonData in json_array:
                        all_data.append(jsonData)
                elif lines.find(':{') > 0:
                    index = lines.index("{")
                    lines = lines[index:len(lines)]
                    json_dict = json.loads(lines)
                    all_data.append(json_dict)
                elif lines[0] == '{' and lines.find('}') > 0:
                    json_dict = json.loads(lines)
                    all_data.append(json_dict)
                elif lines.find('{') > 0 and lines.find('}') > 0:
                    index = lines.index("{")
                    lines = lines[index:len(lines)]
                    json_dict = json.loads(lines)
                    all_data.append(json_dict)
                else:
                    print('文件格式不对')

        all_data.sort(key=lambda f: f["recordTime"])
        if len(all_data) == 0:
            print('文件没有数据')
            return None, None, ''

        first_dict = all_data[0]
        if 'ecg' in first_dict:
            print('ecg数据')

            missing_tick = self.analysis_ecg_loss(all_data)
            return all_data, missing_tick, 'ecg'

        elif 'displayTemp' in first_dict:
            print('temp数据')
            self.analysis_temp_loss(all_data)
            return all_data, [], 'temp'
        elif 'spo2' in first_dict:
            print('血氧数据')
            return all_data, [], 'spo2'
        else:
            print('没有可解析的数据')
            return None, None, ''


    def analysis_ecg_loss(self,all_data):
        missing_tick = []

        for i in range(len(all_data) - 1):
            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
            end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')

            if abs(delta) < 500:
                print(f"duplicated from {start_str} to {end_str}")

            if delta > 1100:
                print(f"part one: missing from {start_str} to {end_str}, count: {delta / 1000 - 1:.0f}")
                missing_tick += [(start_tick, end_tick)]
        return missing_tick

    def analysis_temp_loss(self, all_data):
        last_time = 0
        record_lost_count = 0
        for jsonDic in all_data:
            record_time = jsonDic['recordTime'] / 1000
            if last_time == 0:
                last_time = record_time
                continue
            diff_time = record_time - last_time
            if diff_time < 65:
                last_time = record_time
                continue
            lost_start_time = time.strftime("%Y--%m--%d %H:%M:%S", time.localtime(last_time))
            lost_final_time = time.strftime("%Y--%m--%d %H:%M:%S", time.localtime(record_time))

            print('丢失的时间点区间起点: ' + lost_start_time + ' 终点：' + lost_final_time)
            record_lost_count += diff_time / 64
            last_time = record_time

        first_time = all_data[0]['recordTime'] / 1000
        final_time = all_data[len(all_data) - 1]['recordTime'] / 1000
        diff_all_count = (final_time - first_time) / 64

        accept_rate = 1 - record_lost_count / diff_all_count
        print('理论上每64S都要收到数据的次数=' + str(diff_all_count))
        print('接受率为：' + str(accept_rate))


    def read_mit16_data(self,mit16_path):
        mit16_path_name = mit16_path.replace('.dat', '')
        mit16_path_name = mit16_path_name.replace('.hea', '')
        record = wfdb.rdrecord(mit16_path_name)
        print(record.__dict__)
        start_date_time = record.base_datetime
        print(start_date_time)

        start_time_stamp = int(time.mktime(start_date_time.timetuple()))*1000

        mit_ecg_buffer = record.p_signal
        mit_split_ecg_buffer = [mit_ecg_buffer[i:i+128] for i in range(0, len(mit_ecg_buffer), 128)]

        data_buffer = []
        for ecg_buffer in mit_split_ecg_buffer:
            data_dict = {}
            ecg_array = []
            start_time_stamp += 1000
            for ecg in ecg_buffer:
                ecg_value = ecg[0]*1000
                ecg_array.append(ecg_value)
            acc_array = []
            for j in range(0,5):
                acc_dict = [-1000,-2000,-3000]
                acc_array.append(acc_dict)
            data_dict['ecg'] = ecg_array
            data_dict['recordTime'] = start_time_stamp
            data_dict['hr'] = 60
            data_dict['acc'] = acc_array
            data_dict['flash'] = 0
            data_dict['leadOn'] = 1
            data_dict['rwl'] = [-1]
            data_buffer.append(data_dict)

        return data_buffer

    def read_ppg(self,ppg_path):
        '''
        读取PPG数据
        :param ppg_path:
        :return:
        '''
        ir_array = []
        red_array = []
        with open(ppg_path, 'r') as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break

                index = lines.index("{")
                lines = lines[index:len(lines)]
                json_dict = json.loads(lines)
                ppg_array = json_dict['PPG']
                for ppg_dic in ppg_array:
                    ir = ppg_dic['ir']
                    red = ppg_dic['red']
                    ir_array.append(ir)
                    red_array.append(red)