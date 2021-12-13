#恩识数据与我们数据对比图


import matplotlib.pyplot as plt
import time
import wfdb
from matplotlib import ticker
import numpy as np

TIME_ZONE = np.timedelta64(8, "h")

def get_draw_data(all_data,ECG_HZ):
    raw_ecg_x = [np.datetime64(i["recordTime"], "ms") + TIME_ZONE for i in all_data]
    raw_ecg_y = [i["ecg"] for i in all_data]
    ecg_x = []
    ecg_y = []
    offset = 0
    if ECG_HZ == 256:
        offset = 10
    for i in range(len(raw_ecg_x)):
        if len(raw_ecg_y[i]) != ECG_HZ:
            print(f"wrong ECG length found, padding with zero")
            raw_ecg_y[i] = [0] * ECG_HZ

        for j in range(ECG_HZ):
            raw_x = raw_ecg_x[i] + np.timedelta64(int(j * 1000 / ECG_HZ), "ms")
            raw_y = raw_ecg_y[i][j] - offset*1000
            ecg_x.append(raw_x)
            ecg_y.append(raw_y)
    return ecg_x,ecg_y


def draw_mit_ishne(ensense_data,vivalnk_data):
    ensense_ecg_x,ensense_ecg_y = get_draw_data(ensense_data,256)
    vivalnk_ecg_x,vivalnk_ecg_y = get_draw_data(vivalnk_data,128)
    plt.ylim(-1.5, 2)
    ensense_plt = plt.subplot(211)
    ensense_new_ecg_y = np.array(ensense_ecg_y)
    plt.title("ensense Raw ECG")
    magnification = 1000
    formatter = ticker.FuncFormatter(lambda x, y: f"{x / magnification:.3}mV")
    ensense_plt.yaxis.set_major_formatter(formatter)
    # if self.denoise_waveform:
    #     new_ecg_y = self.remove_baseline_wander(new_ecg_y)
    plt.plot(ensense_ecg_x, ensense_new_ecg_y)

    vivalnk_plt = plt.subplot(212)

    vivalnk_new_ecg_y = np.array(vivalnk_ecg_y)
    plt.title("VivaLNK Raw ECG")
    magnification = 1000
    formatter = ticker.FuncFormatter(lambda x, y: f"{x / magnification:.3}mV")
    vivalnk_plt.yaxis.set_major_formatter(formatter)
    plt.plot(vivalnk_ecg_x, vivalnk_new_ecg_y)

    plt.legend()
    plt.show()


def read_mit16_data(mit16_path,fs):
    '''生成MIT16文件
    :param mit16_path: 携带dat和hea的路径名称
    :return:
    '''
    mit16_path_name = mit16_path.replace('.dat', '')
    mit16_path_name = mit16_path_name.replace('.hea', '')
    record = wfdb.rdrecord(mit16_path_name)
    print(record.__dict__)
    start_date_time = record.base_datetime
    # self.mit_log(start_date_time)
    # 生成文件的起始时间
    start_time_stamp = int(time.mktime(start_date_time.timetuple())) * 1000

    mit_ecg_buffer = record.p_signal
    mit_split_ecg_buffer = [mit_ecg_buffer[i:i + fs] for i in range(0, len(mit_ecg_buffer), fs)]

    data_buffer = []
    for ecg_buffer in mit_split_ecg_buffer:
        data_dict = {}
        ecg_array = []
        start_time_stamp += 1000
        for ecg in ecg_buffer:
            ecg_value = ecg[0] * 1000
            ecg_array.append(ecg_value)
        data_dict['ecg'] = ecg_array
        data_dict['recordTime'] = start_time_stamp

        data_buffer.append(data_dict)

    return data_buffer



if __name__ == "__main__":
    ensense_data = read_mit16_data('/Users/weixu/Documents/维灵/数据分析/波形不稳定数据分析/恩识设备数据/mit16-ensense-1/nalong-1634780733000.dat',256)
    vivalnk_data = read_mit16_data("/Users/weixu/Documents/维灵/数据分析/波形不稳定数据分析/恩识设备数据/download/mit16/VivaLNK-1634780743958.dat",128)

    draw_mit_ishne(ensense_data,vivalnk_data)
