#!/usr/bin/env python
# coding:utf-8

from ScriptTool_analysis.VivaLNK_Reading import ReadFile
from ScriptTool_analysis.ACC_check_bp import caculate_acc_quality
import os
import json

class TestACC():
    def __init__(self):
        print('Test ACC')

    def split_list_by_n(self,list_collection, n):
        """
        将集合均分，每份n个元素
        :param list_collection:
        :param n:
        :return:返回的结果为评分后的每份可迭代对象
        """
        for i in range(0, len(list_collection), n):
            yield list_collection[i: i + n]

    def split_log_file(self,file_name,acc_data):

        index = 0
        for i in range(0, len(file_name)):
            if file_name[i] == '/' or file_name[i] == '\\':
                index = i
        dir_name = file_name[0:index + 1]

        list_acc = self.split_list_by_n(acc_data,60)
        index = 0
        for group in list_acc:
            print(len(group))
            file_name = dir_name+'splic/' + str(index) + '.log'
            index += 1
            with open(file_name, "a+") as output:
                for line_dict in group:
                    json.dump(line_dict, output)
                    output.write('\n')
                output.close()

def printMsg(msg):
    print(msg)

if __name__ == '__main__':
    filepath = '/Users/xuwei/Desktop/ACC硬件对比干扰/C5'
    list = os.listdir(filepath)
    length = len(list)
    batch_path_array = []
    for i in range(0, length):
        path = os.path.join(filepath, list[i])
        if path.find('DS_Store') > 0 or path.find('splic') > 0:
            continue
        batch_path_array.append(path)

    read_file = ReadFile(ReadFile_log=printMsg)
    all_file_data, missing_tick, data_type = read_file.read_batch_files_data(batch_files_array=batch_path_array,
                                                                             compensatory_value=-1)

    test_acc = TestACC()
    test_acc.split_log_file(batch_path_array[0],all_file_data)

    # acc_filepath = filepath +'/splic'
    # acc_list = os.listdir(acc_filepath)
    # acc_path_array = []
    # for i in range(0, len(acc_list)):
    #     path = os.path.join(acc_filepath, acc_list[i])
    #     if path.find('DS_Store') > 0:
    #         continue
    #     acc_path_array.append(path)
    # print(acc_filepath)
    # # 计算SNR
    # caculate_acc_quality(acc_path_array)
