

import os
import matplotlib
import numpy as np
import matplotlib.pyplot as plt

filepath = "/Users/weixu/Downloads/Amplitude/2222"

list = os.listdir(filepath)

length = len(list)
for i in range(0, length):
    file_path_name = os.path.join(filepath, list[i])
    print(file_path_name)
    if file_path_name.find('.DS') >= 0:
        continue
    lines = []
    with open(file_path_name, 'r') as file_to_read:
        lines = file_to_read.readlines()

    ecg_array = []
    for value_str in lines:
        value_int = value_str.replace(',\n', '')
        ecg_array.append(int(value_int))

    plt.figure(i+1)
    # ecg_array = [1,2,3,4,5,6,7,7]
    x = np.linspace(0, len(ecg_array), len(ecg_array))
    plt.plot(x, ecg_array, color='b')

    for j in range(0, len(ecg_array)):
        if j % 128 == 0:
            print(f'j = {j}   y={ecg_array[j]}')
            plt.text(j, ecg_array[j], str(ecg_array[j]), family='serif', style='italic', ha='right', wrap=True)

            # plt.annotate('(%s,%s)' % (j, ecg_array[j]), xy=(j, ecg_array[j]), xytext=(-20, 10),textcoords='offset points')

    # plt.ylim(-1000, 1000)
    plt.title(list[i])
    plt.tick_params(axis='both', labelsize=14)

    plt.show()