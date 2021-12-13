import argparse
import sys
import os
import json
import wfdb
import time
import datetime
import numpy
import re
class ReadFile:
    def __init__(self,ReadFile_log):
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
                    self.ReadFile_log('文件格式不对')



        all_data.sort(key=lambda f: f["recordTime"])
        if len(all_data) == 0:
            self.ReadFile_log('文件没有数据')
            return None, None, ''

        first_dict = all_data[0]
        if 'ecg' in first_dict:
            self.ReadFile_log('ecg数据')

            missing_tick = self.analysis_ecg_loss(all_data)
            return all_data, missing_tick, 'ecg'

        elif 'displayTemp' in first_dict:
            self.ReadFile_log('temp数据')
            # self.analysis_temp_loss(all_data)
            return all_data, [], 'temp'
        elif 'spo2' in first_dict:
            self.ReadFile_log('血氧数据')
            return all_data, [], 'spo2'
        elif 'sys' in first_dict:
            self.ReadFile_log('血压数据')
            return all_data, [], 'bp'
        else:
            self.ReadFile_log('没有可解析的数据')
            return None, None, ''

    # 读取一批文件的数据
    def read_batch_files_data(self,batch_files_array,compensatory_value):
        all_file_data = []
        all_missing_tick = []
        data_type = ''
        for file_path_name in batch_files_array:
            self.ReadFile_log('解析文件:' + file_path_name)

            data_buffer, single_missing_tick, type = self.read_file_data(file_path_name)
            if data_buffer is None or len(data_buffer) == 0:
                self.ReadFile_log(file_path_name + '文件为空')
                continue
            data_type = type

            for file_dict in data_buffer:
                all_file_data.append(file_dict)
            for file_missing_dict in single_missing_tick:
                all_missing_tick.append(file_missing_dict)

        # -1是不需要将缺失的值补偿 补偿是生成mit16的做法
        if compensatory_value != -1:
            # print(all_missing_tick)
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

    def analysis_data_loss(self, all_data, data_type):
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
        record_minute = startTime / 1000 / 60
        miss_minute = 0
        # 丢失列表
        missing_tick = []
        for i in range(len(all_data) - 1):
            end_tick = all_data[i + 1]["recordTime"]
            start_tick = all_data[i]["recordTime"]
            delta = end_tick - start_tick
            if abs(delta) < 500:
                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f"duplicated from {start_str} to {end_str}")

            if delta > miss_mill_scope:
                # print(delta, miss_mill_scope)
                start_str = datetime.datetime.fromtimestamp(start_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                end_str = datetime.datetime.fromtimestamp(end_tick / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(
                    f"part one: missing from {start_str} to {end_str}, count: {(delta / 1000) / caculate_miss - 1:.0f}")
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
                diff_minute = end_tick / 1000 / 60 - record_minute
                if diff_minute >= 2:
                    miss_minute += diff_minute - 1
                record_minute = end_tick / 1000 / 60

            if 'receiveTime' in all_data[i]:
                receive_time = all_data[i]['receiveTime']
                if min_receive == 0:
                    min_receive = receive_time
                    max_receive = receive_time
                else:
                    if receive_time < min_receive:
                        min_receive = receive_time
                    if receive_time > max_receive:
                        max_receive = receive_time

        # lead off的日志
        if lead_off_count != 0:
            self.ReadFile_log(f'lead off times:{lead_off_count}')
            for lead_off_time in lead_off_time_set:
                lead_off_time_str = datetime.datetime.fromtimestamp(lead_off_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                self.ReadFile_log(f'Every time the lead falls off:{lead_off_time_str}')
        # 丢失统计
        theory_count = (endTime - startTime) / 1000 + 1
        theory_count = int(theory_count / caculate_miss)
        self.ReadFile_log(f"Theoretical number:{theory_count}")  # 理论数量
        self.ReadFile_log(f"Actual number:{len(all_data)}")  # 实际数量
        theory_missing = int(theory_count - len(all_data))
        self.ReadFile_log(f"Query the number of theoretical losses in the time range: {theory_missing}")  # 查询时间范围理论丢失数量
        scope_count = (all_data[len(all_data) - 1]['recordTime'] / 1000 - zero_dict[
            'recordTime'] / 1000) / caculate_miss
        self.ReadFile_log(
            f"Query time range actual data start and end lost quantity: {int(scope_count) - len(all_data)}")  # 查询时间范围实际数据起始结束丢失数量
        # 丢失率分析
        if data_type == 'temp':
            every_data_rate = len(all_data) / theory_count
            total_minute = last_dict['recordTime'] / 1000 / 60 - zero_dict['recordTime'] / 1000 / 60 - 1
            minute_rate = 1 - miss_minute / total_minute
            self.ReadFile_log(f'Acceptance rate of all broadcasts:{every_data_rate}')  # 所有广播的接受率
            self.ReadFile_log(f'Minute acceptance rate:{minute_rate}')  # 分钟接收率

        # 这段数据上传所用的时间
        if min_receive != 0:
            min_receive_str = datetime.datetime.fromtimestamp(min_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
            max_receive_str = datetime.datetime.fromtimestamp(max_receive / 1000).strftime('%Y-%m-%d %H:%M:%S')
            total_receivce_time = (max_receive - min_receive) / 1000
            self.ReadFile_log(
                f"This piece of data upload server receiving time:{min_receive_str},{max_receive_str},共花费{int(total_receivce_time)}S")  # 此段数据上传服务端接收时间

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

class ProcessMitData():
    def __init__(self,mit_log):
        self.mit_log = mit_log

    def read_mit16_data(self,mit16_path):
        '''生成MIT16文件
        :param mit16_path: 携带dat和hea的路径名称
        :return:
        '''
        mit16_path_name = mit16_path.replace('.dat', '')
        mit16_path_name = mit16_path_name.replace('.hea', '')
        record = wfdb.rdrecord(mit16_path_name)
        print(record.__dict__)
        start_date_time = record.base_datetime
        self.mit_log(start_date_time)
        # 生成文件的起始时间
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
            data_dict['ecg'] = ecg_array
            data_dict['recordTime'] = start_time_stamp

            data_buffer.append(data_dict)

        return data_buffer

    def generate_mit_file(self, record_name, sample_frequency, amplitudes, ecg_list, start_record_mills, tzinfo,output_dir_path):
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
            base_datetime = datetime.datetime.fromtimestamp(start_record_mills / 1000)
            base_date = base_datetime.date()
            base_time = base_datetime.time()
            wfdb.wrsamp(record_name, sample_frequency, units, signal_name, d_signal=numpy.array(digital_signals),
                        fmt=formats, adc_gain=adc_gains, baseline=baselines, base_date=base_date, base_time=base_time,
                        write_dir=output_dir_path)
            header_file_path = os.path.join(output_dir_path, record_name + '.hea')
            data_file_path = os.path.join(output_dir_path, record_name + '.dat')
            self.mit_log('mit16文件生成 ' + header_file_path + ' ' + data_file_path)
            file_line = ''
            with open(header_file_path,'r') as file_to_read:
                while True:
                    line = file_to_read.readline()
                    if not line:
                        break
                    print(line)
                    result = self.deleteByStartAndEnd(line,'.',' ')
                    if file_line == '':
                        file_line += result
                    else:
                        file_line = file_line+result
            with open(header_file_path,'w') as f:
                f.write(file_line)



    def deleteByStartAndEnd(self,s, start, end):
        # 找出两个字符串在原始字符串中的位置，开始位置是：开始始字符串的最左边第一个位置，结束位置是：结束字符串的最右边的第一个位置
        if s.find('.dat') > 0:
            return s
        x1 = s.index(start)
        if x1 < 0:
            return s
        all_index = [substr.start() for substr in re.finditer(end, s)]
        x2 = all_index[len(all_index) - 1]
        # 找出两个字符串之间的内容
        x3 = s[x1:x2]
        # 将内容替换为控制符串
        result = s.replace(x3, "")
        print(result)
        return result

class ToolClass:
    def __init__(self):
        pass

    def get_current_file_directory(self,file_name):
        '''获取当前文件的目录
        @param file_name 文件名
        :return 目录路径
        '''
        index = 0
        for i in range(0, len(file_name)):
            if file_name[i] == '/' or file_name[i] == '\\':
                index = i
        dir_name = file_name[0:index + 1]
        return dir_name
def print_msg(msg):
    print(msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filePath",type=str, help="json folder path, required")
    parser.add_argument("-o", "--output",type=str, help="The output file path, required")
    parser.add_argument('-n',"--mitName",type=str, help="The name of the generated mit16 file, required")
    parser.add_argument('--verbose', '-v', action='store_true', help='version')

    parser.add_argument('rest', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    # print(args)
    print(args.filePath)

    if args.verbose:
        print("Version:V1.4")

    if args.filePath is None:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.filePath):
        print('The input folder does not exist！！！')

    if args.output is None:
        parser.print_help()
        sys.exit(1)

    if args.mitName is None:
        parser.print_help()
        sys.exit(1)
    else:
        if not os.path.exists(args.output):
            print('The output folder does not exist！！！')
            sys.exit(1)

    file_parh_array = []
    list = os.listdir(args.filePath)

    for i in range(0, len(list)):
        file_path_name = os.path.join(args.filePath, list[i])
        if file_path_name.find('.DS') >= 0:
            continue
        file_parh_array.append(file_path_name)
    print(file_parh_array)

    read_file = ReadFile(print_msg)
    all_file_data,miss_data,data_type = read_file.read_batch_files_data(file_parh_array,compensatory_value=8.7)

    # 获取文件夹路径
    # tooClass = ToolClass()
    # file_name = file_parh_array[0]
    # dir_name = tooClass.get_current_file_directory(file_name)

    if data_type == 'ecg':
        ecg_buffer = []
        mit16_start_time = 0
        for dict in all_file_data:
            if mit16_start_time == 0:
                mit16_start_time = dict['recordTime']
            ecg_array = dict['ecg']
            # ecg_array = json.loads(ecg_array_str)
            for ecg_value in ecg_array:
                if ecg_value == None:
                    ecg_buffer.append(8700)
                else:
                    if int(ecg_value)>32767 or int(ecg_value)<-32768:
                        print(ecg_value)
                    ecg_buffer.append(int(ecg_value))

        ecg_all = []
        ecg_all.append(ecg_buffer)
        write_dir = args.output
        # write_dir = os.path.join(args.output,'mit16')
        print(write_dir)
        # if not os.path.exists(write_dir):
        #     os.makedirs(write_dir, exist_ok=True)

        process_mit = ProcessMitData(mit_log=print_msg)
        process_mit.generate_mit_file(args.mitName, 128, [1000], ecg_all, mit16_start_time,
                                      None, write_dir)



