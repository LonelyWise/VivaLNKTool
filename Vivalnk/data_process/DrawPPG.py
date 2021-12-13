# -*- coding: utf-8 -*-
"""
画PPG波形的工具
"""
import os
import json
import matplotlib.pyplot as plt
import numpy as np

ir_array = []
red_array = []

wave_form_array = []
def read_file_data(path):
    with open(path,'r') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break
            if lines.find("[SpO2:RTWave]") < 0:
                continue
            index = lines.index("{")
            lines = lines[index:len(lines)]
            json_dict = json.loads(lines)
            ppg_array = json_dict['waveform']

            for value in ppg_array:
                wave_form_array.append(value)

            # for ppg_dic in ppg_array:
            #     ir = ppg_dic['ir']
            #     red = ppg_dic['red']
            #     ir_array.append(ir)
            #     red_array.append(red)

    plt.figure(1)
    x = np.linspace(1, len(wave_form_array), len(wave_form_array), endpoint=True)
    ax = plt.subplot(1, 1, 1)
    plt.sca(ax)
    plt.plot(x, wave_form_array, color='g')
    plt.ylim(40, 180)
    plt.xlabel("Times")
    plt.ylabel("ir")
    plt.title("IR Wave")

    # y = np.linspace(1, len(red_array), len(red_array), endpoint=True)
    # ay = plt.subplot(2, 1, 2)
    # plt.sca(ay)
    # plt.plot(y, red_array, color='b')
    # plt.ylim(80000, 160000)
    # plt.xlabel("Times")
    # plt.ylabel("red")
    # plt.title("Red Wave")

    plt.show()


if __name__ == "__main__":
    read_file_data('/Users/weixu/Desktop/VVSpO2Log.log')