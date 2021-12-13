from scipy import ndimage
import os
import numpy as np
from ScriptTool_analysis.ACC_vlio import read_recording
from scipy import signal, stats
import ScriptTool_analysis.ACC_processing
import matplotlib.pyplot as plt
# plt.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei', 'FangSong']  # 汉字字体,优先使用楷体，如果找不到楷体，则使用黑体
# plt.rcParams['font.size'] = 12  # 字体大小
# plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

def get_diff(sig, FS_ACC):
    # Calculate min and max envelopes for ACC amplitude
    upper = ndimage.maximum_filter1d(sig, size=int(2*FS_ACC))
    lower = -ndimage.maximum_filter1d(-sig, size=int(2*FS_ACC))
    diff = upper - lower
    return diff

def signaltonoise(a, axis=0, ddof=0):
    a = np.asanyarray(a)
    m = a.mean(axis)
    sd = a.std(axis=axis, ddof=ddof)
    return np.where(sd == 0, 0, m/sd)

good_count = 0
total_count = 0
def caculate_acc_quality(file_path_array):
    global total_count
    global good_count
    total_snr = 0
    for file_path_name in file_path_array:
        if 'log' in file_path_name:
            total_count += 1
            print(file_path_name)
            # Get recording

            rec = read_recording(file_path_name)

            total_snr += calculate_acc_snr(file_path_name,rec.x,rec.y,rec.z,show_wave=False)

        # next = input('Continue? (y/n): ')
        # if next == 'y':
        #     pass
        # else:
        #     break
    print(f'Total={total_count}  Good={good_count}  {good_count/total_count}   {total_snr}')

def calculate_acc_snr(file_path_name,acc_x,acc_y,acc_z,show_wave):
    global good_count
    FS_ACC = 500

    # Get filtered acc signal
    b, a = signal.butter(2, Wn=[2 / (FS_ACC / 2), 40 / (FS_ACC / 2)], btype="bandpass")
    x_filt = signal.filtfilt(b, a, acc_x)
    y_filt = signal.filtfilt(b, a, acc_y)
    z_filt = signal.filtfilt(b, a, acc_z)
    acc = ACC_processing.get_pca(x_filt, y_filt, z_filt)

    high_noise = []
    # Get High Noise
    for i in range(FS_ACC, len(acc) - FS_ACC, FS_ACC):
        noise_stats = abs(np.mean(acc[i - FS_ACC:i + 2 * FS_ACC]) / np.std(acc[i - FS_ACC:i + 2 * FS_ACC]))
        noise = signaltonoise(acc[i - FS_ACC:i + 2 * FS_ACC])
        high_noise.append(abs(noise))

    # Plot Noise and ACC
    snr = np.mean(high_noise) * 100
    if snr >= 1:
        color = 'r'
        text = 'Bad Signal: Please Reposition Patch'
    else:
        good_count += 1
        color = 'g'
        text = 'Good Signal'

    if show_wave:
        split_array = file_path_name.split('/')
        title_name = split_array[len(split_array) - 1]
        plt.figure(figsize=(12, 8))
        plt.suptitle('{}\nSNR: {}\n{}'.format(title_name, round(snr, 2), text), color=color)
        ax1 = plt.subplot(2, 1, 1)
        ax2 = plt.subplot(2, 1, 2)
        t_acc = np.arange(0, len(acc) / FS_ACC, 1 / FS_ACC)
        ax1.plot(t_acc, acc)
        ax2.plot(high_noise)
        # plt.show()
    print(f'SNR:{round(snr, 2)}    {text}')
    return round(snr, 2)
if __name__ == '__main__':
    dir = "/Users/cyanxu/Documents/维灵/BP-ECG 13轮数据采集/Cjay-上"
    os.chdir(dir)
    FS_ACC = 500
    for filename in [file for file in os.listdir(dir) if 'log' in file]:
        if 'log' in filename:
            print(filename)
            # Get recording
            high_noise = []
            rec = read_recording(filename)

            # Get filtered acc signal
            b, a = signal.butter(2, Wn=[2 / (FS_ACC / 2), 40 / (FS_ACC / 2)], btype="bandpass")
            x_filt = signal.filtfilt(b, a, rec.x)
            y_filt = signal.filtfilt(b, a, rec.y)
            z_filt = signal.filtfilt(b, a, rec.z)
            acc = ACC_processing.get_pca(x_filt, y_filt, z_filt)

            # Get High Noise
            for i in range(FS_ACC, len(acc)-FS_ACC, FS_ACC):
                noise_stats = abs(np.mean(acc[i - FS_ACC:i + 2 * FS_ACC])/np.std(acc[i - FS_ACC:i + 2 * FS_ACC]))
                noise = signaltonoise(acc[i - FS_ACC:i + 2 * FS_ACC])
                high_noise.append(abs(noise))

            # Plot Noise and ACC
            snr = np.mean(high_noise)*100
            if snr >= 1:
                color='r'
                text = 'Bad Signal: Please Reposition Patch'

            else:
                color='g'
                text = 'Good Signal'
            # plt.figure(figsize=(12,8))
            # plt.suptitle('{}\nSNR: {}\n{}'.format(filename, round(snr, 2), text), color=color)
            # ax1 = plt.subplot(2,1,1)
            # ax2 = plt.subplot(2,1,2)
            # t_acc = np.arange(0, len(acc) / FS_ACC, 1 / FS_ACC)
            # ax1.plot(t_acc, acc)
            # ax2.plot(high_noise)
            # plt.show()
            print(f'SNR:{round(snr, 2)}    {text}')
        next = input('Continue? (y/n): ')
        if next == 'y':
            pass
        else:
            break