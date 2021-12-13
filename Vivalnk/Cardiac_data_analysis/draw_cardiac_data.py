import os
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as mp
import matplotlib.dates as mdate
import matplotlib.ticker as mtick

class DrawWave:
    def __init__(self):
        pass

    def draw_acc(self,x_array,y_array,z_array):
        plt.figure(1)
        x = np.linspace(1, len(x_array), len(x_array), endpoint=True)
        ax = plt.subplot(3, 1, 1)
        plt.sca(ax)
        plt.plot(x, x_array, color='g')
        plt.ylim(-2000, 2000)
        plt.xlabel("Times")
        plt.ylabel("x")
        plt.title("X Wave")

        y = np.linspace(1, len(y_array), len(y_array), endpoint=True)
        ay = plt.subplot(3, 1, 2)
        plt.sca(ay)
        plt.plot(y, y_array, color='b')
        plt.ylim(-2000, 2000)
        plt.xlabel("Times")
        plt.ylabel("y")
        plt.title("Y Wave")

        z = np.linspace(1, len(z_array), len(z_array), endpoint=True)
        az = plt.subplot(3, 1, 3)
        plt.sca(az)
        plt.plot(z, z_array, color='r')
        plt.ylim(-2000, 2000)
        plt.xlabel("Times")
        plt.ylabel("z")
        plt.title("Z Wave")

        plt.show()


    def draw_ecg(self,ecg_array,rwl_array,time_array):
        x_lenth = len(ecg_array) / 128
        print(x_lenth)
        pltecg = plt.subplot(2, 1, 1)
        plt.sca(pltecg)
        x = np.linspace(0, x_lenth, len(ecg_array), endpoint=True)
        x_array = []
        x_count = 1
        for j in time_array:
            x_array.append(x_count);
            x_count += 1
        plt.plot(x, ecg_array)
        plt.xticks(x_array, time_array)
        for i in range(0, len(rwl_array) - 1):
            x0 = rwl_array[i]
            y0 = ecg_array[x0]
            x0 = x0 / 128
            plt.scatter(x0, y0, s=20, color='r', marker='*')  # 散点图
        plt.xlabel("Times")
        plt.ylabel("ECG")
        plt.title("ECG Wave")
        plt.ylim(-4, 4)

        plt.legend()  # 显示左下角的图例

        plt.show()

    def draw_hr(self,hr_array):
        x = np.linspace(1,len(hr_array), len(hr_array), endpoint=True)
        plt.plot(x, hr_array)

        plt.xlabel("Times")
        plt.ylabel("HR")
        plt.title("HR Wave")

        plt.ylim(0, 100)

        plt.legend()  # 显示左下角的图例

        plt.show()

