

import os
import json
import vlio
from datetime import datetime
import processing
import activity
import noise
import qrs
import HrFile
import XMLAnalysis

class DataHandle():
    '''用于处理json数据，输出csv文件'''
    def __init__(self):
        self.first_time = 0
        pass

    def read_json_file(self,input_file_name):
        packets = []

        recordtime_array = []
        rr_array = []
        hr_array = []
        # file_name = "/Users/weixu/Documents/维灵/标记绘图/json_xml_3_pairs/1629085490089-1629091666089_denoised.json"

        with open(input_file_name, 'r') as file_to_read:
            while True:
                lines = file_to_read.readline()
                if not lines:
                    break

                json_array = json.loads(lines)
                i = 0
                for json_dict in json_array:
                    if self.first_time == 0:
                        self.first_time = int(json_dict['recordTime'])
                    recordtime_array.append(int(json_dict['recordTime']))
                    rr_array.append(json_dict['rr'])
                    hr_array.append(json_dict['hr'])
                    timestamp = str(datetime.fromtimestamp(int(json_dict['recordTime']) / 1000))[:-3]
                    new_acc = []
                    acc = json_dict['acc']
                    for a in acc:
                        new_line = [a['y'], a['x'], a['z']]
                        new_acc.append(new_line)
                    json_dict['acc'] = new_acc
                    packets.append(vlio.Packet(timestamp, json_dict, i + 1))
                    i += 1

        # 获取病症时间信息
        xml_file_name = input_file_name.replace(".json", ".xml")
        rhythm = XMLAnalysis.RhythmObtain()
        rhythm_list = rhythm.obtainRhythm(self.first_time, xml_file_name)
        print(rhythm_list)

        recording = vlio.Recording(packets, input_file_name)
        activity_instance = activity.ActivityInstance()
        noise_instance = noise.NoiseInstance()
        qrs_instance = qrs.QRSInstance()
        hr_instance = HrFile.HRInstance()

        FS_ACC = 5
        FS_ECG = 128
        magnification = 1000

        ecg = recording.ecg * magnification
        x = recording.x
        y = recording.y
        z = recording.z
        x_filt, y_filt, z_filt = processing.get_filtered(x, y, z, FS_ACC)
        acc = processing.get_pca(x_filt, y_filt, z_filt)

        # Get calibration
        x_cal = x_filt[0:(FS_ACC * 10)]
        y_cal = y_filt[0:(FS_ACC * 10)]
        z_cal = z_filt[0:(FS_ACC * 10)]
        acc_cal = processing.get_pca(x_cal, y_cal, z_cal)

        # Get Activity
        all_activities = []
        for i in range(FS_ACC, len(x) - FS_ACC, FS_ACC):
            activity_result = activity.detect_activity(acc[i - FS_ACC:i + 2 * FS_ACC], acc_cal, FS_ACC,
                                                       activity_instance, win_len=2)
            all_activities.append(activity_result.max_activity)
        act = activity.get_diff(acc, FS_ACC)
        act = [int(a * 1000) for a in act]

        # Get Low and High Activity
        i = 0
        gap = int(len(act) / len(all_activities))
        activity_array = []
        start = []
        stop = []
        for a in all_activities:
            if a == 'high_activity':
                start.append(i)
                stop.append(i + gap)
                activity_array.append(2)
            elif a == 'low_activity':
                start.append(i)
                stop.append(i + gap)
                activity_array.append(1)
            else:
                start.append(i)
                stop.append(i + gap)
                activity_array.append(0)
                pass
            i += gap

        # cutoff = pd.DataFrame({'start':start, 'stop':stop, 'index':index})
        # print(cutoff)

        # Get HR and HRV
        hr_all = []
        hrv_all = []
        for i in range(FS_ECG, len(ecg) - FS_ECG, FS_ECG):
            noise_result = noise.detect_noise(ecg[i - FS_ECG:i + 2 * FS_ECG], 3 * FS_ECG, FS_ECG, magnification,
                                              noise_instance)
            qrs_result = qrs.detect_qrs(ecg[i - FS_ECG:i + 2 * FS_ECG], 3 * FS_ECG, FS_ECG, magnification,
                                        noise_result.saturation, noise_result.high_noise, noise_result.low_noise,
                                        qrs_instance)
            hr_result = HrFile.detect_hr(qrs_result.rri, 5, hr_instance)

            hr_all.append(hr_result.hr)
            hrv_all.append(hr_result.hrv)
        # print(hrv_all)

        print(f"packets len ={len(packets)}")

        write_path_name = input_file_name.replace('.json', '.csv')
        with open(write_path_name, "w") as output:
            output.write('time,hr,hrv,rr,activity,rhythm\n')

            for i in range(len(activity_array)):
                recordTime_value = recordtime_array[i]
                recordtime_str = str(recordTime_value)
                hr_str = str(hr_array[i])
                rr_str = str(rr_array[i])
                hrv_str = str(hrv_all[i])
                activity_str = str(activity_array[i])

                rhythm_info = "--"
                for rhythm_item in rhythm_list:
                    start_time = rhythm_item[0]
                    end_time = rhythm_item[1]
                    if int(recordTime_value/1000) >= start_time and int(recordTime_value/1000) <= end_time:
                        rhythm_info = rhythm_item[2]

                write_value = recordtime_str + ',' + hr_str + ',' + hrv_str + ',' + rr_str + ',' + activity_str + ',' + rhythm_info + '\n'
                # print(write_value)
                output.write(write_value)
            output.close()