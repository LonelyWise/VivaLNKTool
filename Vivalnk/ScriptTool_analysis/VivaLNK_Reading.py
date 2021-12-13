#!/usr/bin/env python 
# coding:utf-8
import json
import datetime
import time
import wfdb
import codecs

class ReadFile:
    def __init__(self, ReadFile_log):
        self.ReadFile_log = ReadFile_log
        # self.ReadFile_log('开始读取文件数据')

    # 读取单个文件的数据
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
                    self.ReadFile_log('file format is error')

        all_data.sort(key=lambda f: f["recordTime"])
        if len(all_data) == 0:
            self.ReadFile_log('File no data')
            return None, None, ''

        first_dict = all_data[0]
        if 'ecg' in first_dict:
            self.ReadFile_log('ECG data')
            missing_tick = self.analysis_ecg_loss(all_data)
            return all_data, missing_tick, 'ecg'
        elif 'display' in first_dict or 'displayTemp' in first_dict:
            self.ReadFile_log('temperature data')
            # self.analysis_temp_loss(all_data)
            return all_data, [], 'temp'
        elif 'spo2' in first_dict:
            self.ReadFile_log('SpO2 data')
            return all_data, [], 'spo2'
        elif 'sys' in first_dict:
            self.ReadFile_log('BP data')
            return all_data, [], 'bp'
        else:
            self.ReadFile_log('No parsable file')
            return None, None, ''

    # 读取一批文件的数据
    def read_batch_files_data(self,batch_files_array,compensatory_value):
        all_file_data = []
        all_missing_tick = []
        data_type = ''
        for file_path_name in batch_files_array:
            self.ReadFile_log('Analyse file:' + file_path_name)

            data_buffer, single_missing_tick, type = self.read_file_data(file_path_name)
            if data_buffer is None or len(data_buffer) == 0:
                self.ReadFile_log(file_path_name + ' file is empty')
                continue
            data_type = type

            for file_dict in data_buffer:
                all_file_data.append(file_dict)
            for file_missing_dict in single_missing_tick:
                all_missing_tick.append(file_missing_dict)

        # -1是不需要将缺失的值补偿 补偿是生成mit16的做法
        if compensatory_value != -1:
            print(all_missing_tick)
            compensatory_Array = []
            array_count = 128
            while array_count > 0:
                compensatory_Array.append(compensatory_value)
                array_count -= 1

            for miss_tuple in all_missing_tick:
                st = int(miss_tuple[0]) + 1000
                et = int(miss_tuple[1])
                while st < et:
                    miss_dict = {}
                    miss_dict['ecg'] = compensatory_Array
                    miss_dict['recordTime'] = st
                    miss_dict['flash'] = 1
                    all_file_data.append(miss_dict)
                    st += 1000

        all_file_data.sort(key=lambda f: f["recordTime"])

        ecg_missing_tick = self.analysis_data_loss(all_file_data,data_type)

        return all_file_data,ecg_missing_tick,data_type

    def analysis_data_loss(self,all_data,data_type):
        caculate_miss = 1
        miss_mill_scope = 1050
        if data_type == 'ecg':
            pass
        elif data_type == 'temp':
            # 目前F开头的都是VV200-6的
            if data_type.find('F') >= 0:
                caculate_miss = 12
                miss_mill_scope = 25000
            else:
                caculate_miss = 16
                miss_mill_scope = 33000
        elif data_type == "spo2":
            caculate_miss = 4
            miss_mill_scope = 4500

        zero_dict = all_data[0]
        last_dict = all_data[len(all_data) - 1]
        startTime = zero_dict['recordTime']
        endTime = last_dict['recordTime']
        # 云端接收时间分析
        min_receive = 0
        max_receive = 0
        # lead off统计
        last_lead_status = 1
        lead_off_count = 0
        lead_off_time_set = []
        # 用于体温的分钟接收率
        record_minute = startTime/1000/60
        miss_minute = 0
        # 丢失列表
        missing_tick = []

        rf_count = 0
        real_total = 0
        last_appear = 0
        time_value = 1621569600000
        tiger = 1
        for i in range(len(all_data) - 1):
            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            if abs(delta) < 500:
                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f"duplicated from {start_str} to {end_str}")

            if delta > miss_mill_scope:

                # 丢失时间从lead on到lead on，不能算lead off
                value = 0
                if 'leadOn' in all_data[i]:
                    value = i
                    while (all_data[value]['leadOn'] == 0):
                        value -= 1
                if value != 0:
                    start_tick = all_data[value]["recordTime"]

                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f"part one: missing from {start_str} to {end_str}, count: {(delta / 1000) / caculate_miss - 1:.0f}")
                missing_tick += [(start_tick, end_tick)]


            if 'leadOn' in all_data[i]:
                lead_status = all_data[i]['leadOn']
                if lead_status == 0:
                    if last_lead_status == 1:
                        lead_off_time_set.append(start_tick)
                        lead_off_count += 1
                    else:
                        if (start_tick - lead_off_time_set[len(lead_off_time_set) - 1]) >= 10000:
                            lead_off_time_set.append(start_tick)
                            lead_off_count += 1
                last_lead_status = lead_status

            if data_type == 'temp':
                diff_minute = end_tick/1000/60 - record_minute
                if diff_minute >= 2:
                    miss_minute += diff_minute-1
                record_minute = end_tick/1000/60


            if 'receiveTime' in all_data[i]:
                receive_time = all_data[i]['receiveTime']
                recor_ttime = all_data[i]['recordTime']

                # judge = 0
                # if recor_ttime >= time_value- 24*3600*100 and recor_ttime <= time_value- 18*3600*1000:
                #     judge = 1
                # if recor_ttime >= time_value and recor_ttime <= time_value+6*3600*1000:
                #     judge = 1
                # if recor_ttime >= time_value+24*3600*1000 and recor_ttime <= time_value+30*3600*1000:
                #     judge = 1
                # if recor_ttime >= time_value+48*3600*1000 and recor_ttime <= time_value+54*3600*1000:
                #     judge = 1
                # if recor_ttime >= time_value+72*1000*3600 and recor_ttime <= time_value + 78 * 3600 * 1000:
                #     judge = 1
                # if judge == 0:
                #     continue
                #
                # if receive_time - recor_ttime > 39000:
                #     if last_appear == 0:
                #         last_appear = recor_ttime
                #     else:
                #         if recor_ttime - last_appear < 5000:
                #             # print('同一次断连导致')
                #             if tiger == 1:
                #                 tiger = 0
                #                 red_str = datetime.datetime.fromtimestamp(recor_ttime / 1000).strftime(
                #                     '%Y-%m-%d %H:%M:%S')
                #                 rec_str = datetime.datetime.fromtimestamp(receive_time / 1000).strftime(
                #                     '%Y-%m-%d %H:%M:%S')
                #                 print(f'在手机上接收时间{rec_str}   接收的数据时间为:{red_str}')
                #                 diff_time_value = (receive_time - recor_ttime) / 1000
                #                 print(diff_time_value)
                #         else:
                #             tiger = 1
                #             appear_time_value = (recor_ttime - last_appear) / 1000
                #             print(f'超过相邻时间的统计   {appear_time_value}')
                #
                #
                #             real_total += 1
                #         last_appear = recor_ttime
                #
                #
                #     rf_count += 1

                if min_receive == 0:
                    min_receive = receive_time
                    max_receive = receive_time
                else:
                    if receive_time < min_receive:
                        min_receive = receive_time
                    if receive_time > max_receive:
                        max_receive = receive_time

        # print(f'共出现了：{rf_count}次')
        # print(f'真实出现了：{real_total}次')
        # lead off的日志
        if lead_off_count != 0:
            self.ReadFile_log(f'lead off times:{lead_off_count}')
            for lead_off_time in lead_off_time_set:
                lead_off_time_str = datetime.datetime.fromtimestamp(lead_off_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f'Every time the lead falls off:{lead_off_time_str}')
        #丢失统计
        theory_count = (endTime - startTime) / 1000 + 1
        theory_count = int(theory_count / caculate_miss)
        self.ReadFile_log(f"Theoretical number:{theory_count}") #理论数量
        self.ReadFile_log(f"Actual number:{len(all_data)}") #实际数量
        theory_missing = int(theory_count - len(all_data))
        self.ReadFile_log(f"Query the number of theoretical losses in the time range: {theory_missing}") #查询时间范围理论丢失数量
        scope_count = (all_data[len(all_data) - 1]['recordTime'] / 1000 - zero_dict['recordTime'] / 1000) / caculate_miss +1
        self.ReadFile_log(f"Query time range actual data start and end lost quantity: {int(scope_count) - len(all_data)}") #查询时间范围实际数据起始结束丢失数量
        #丢失率分析
        if data_type == 'temp':
            every_data_rate = len(all_data)/theory_count
            total_minute = last_dict['recordTime']/1000/60 - zero_dict['recordTime']/1000/60 - 1
            minute_rate = 1-miss_minute/total_minute
            self.ReadFile_log(f'Acceptance rate of all broadcasts:{every_data_rate}') #所有广播的接受率
            self.ReadFile_log(f'Minute acceptance rate:{minute_rate}') #分钟接收率

        # 这段数据上传所用的时间
        if min_receive != 0:
            min_receive_str = datetime.datetime.fromtimestamp(min_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
            max_receive_str = datetime.datetime.fromtimestamp(max_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
            total_receivce_time = (max_receive - min_receive)/1000
            self.ReadFile_log(f"This piece of data upload server receiving time:{min_receive_str},{max_receive_str},spending {int(total_receivce_time)} second") #此段数据上传服务端接收时间

        return missing_tick

    # 分析ecg数据丢失
    def analysis_ecg_loss(self,all_data):
        missing_tick = []

        for i in range(len(all_data) - 1):
            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
            end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')

            # if abs(delta) < 500:
            #     self.ReadFile_log(f"duplicated from {start_str} to {end_str}")

            if delta > 1100:
                # self.ReadFile_log(f"part one: missing from {start_str} to {end_str}, count: {delta / 1000 - 1:.0f}")
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

            self.ReadFile_log('丢失的时间点区间起点: ' + lost_start_time + ' 终点：' + lost_final_time)
            record_lost_count += diff_time / 64
            last_time = record_time

        first_time = all_data[0]['recordTime'] / 1000
        final_time = all_data[len(all_data) - 1]['recordTime'] / 1000
        diff_all_count = (final_time - first_time) / 64

        accept_rate = 1 - record_lost_count / diff_all_count
        self.ReadFile_log('理论上每64S都要收到数据的次数=' + str(diff_all_count))
        self.ReadFile_log('接受率为：' + str(accept_rate))

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
            # data_dict['hr'] = 60
            # data_dict['acc'] = acc_array
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


    def read_nb_file_content(self,file_name):
        '''读取nb文件的数据
        :param file_name:
        :return:
        '''
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
        self.ReadFile_log('nb文件解析完成')

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

        self.ReadFile_log('ecg数据解析完成')
        ecg_data = []

        ecg_all = []
        ecg_all.append(real_ecg)

        # 生成mit16的文件
        # self.generate_mit_file('nalong'+'-'+str(self.mit_start_time), 128, [1000], ecg_all, self.mit_start_time, None, self.dir_path + 'mit16/')

        return ecg_all


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


def printMsg(msg):
    print(msg)

if __name__ == '__main__':

    # import os
    # fp = open('/Users/weixu/Desktop/123.txt','a+')
    # filepath = '/Users/weixu/Desktop/123'
    # list = os.listdir(filepath)
    #
    # length = len(list)
    # for i in range(0, length):
    #     file_path_name = os.path.join(filepath, list[i])
    #
    #     with open(file_path_name,'r') as file_to_read:
    #         while True:
    #             line = file_to_read.readline()
    #             if not line:
    #                 break
    #             if line.find('ECGRec_201848/C600106') > 0:
    #                 # index = line.index("{")
    #                 # line = line[index:len(line)]
    #
    #                 fp.write(line)
    # fp.close()

    read_file = ReadFile(printMsg)
    all_data,miss,type = read_file.read_file_data('/Users/weixu/Desktop/长胶贴 贴上面.txt')



    # rr_batch = 0
    # hr_zero = 0
    # total_count = 0
    # for dict in all_data:
    #     total_count += 1
    #     time = dict['recordTime']
    #     rr = dict["rr"]
    #     hr = dict['hr']
    #     rri = dict['rri']
    #     if rr == 0:
    #         rr_batch += 1
    #     if hr == 0:
    #         hr_zero += 1
    #
    #     print(f"时间 = {time}，   {rr}  ,{hr}  ,{rri}")
    #
    # print(f'total count={total_count},  rr zero = {rr_batch}, hr zero = {hr_zero}')