#!/usr/bin/env python
# coding:utf-8
'''
1.直接下载ECG、Temp和SpO2数据画图工具
2.选择文件画图工具
'''
import time
from tkinter import *
import tkinter.filedialog
import sys
import os
# 保证ScriptTool_analysis模块导入不会报错   错误内容：ModuleNotFoundError: No module named 'ScriptTool_analysis'
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from DrawingWaveforms.DrawView import DrawingView
from DrawingWaveforms.ReadFileData import ReadFile


LOG_LINE_NUM = 0

class MY_GUI():
    def __init__(self):
        # init_window_name = init_window_name
        print()

    # 设置窗口
    def set_init_window(self, init_window_name):

        init_window_name.title("分析数据工具")  # 窗口名
        width = 700
        height = 700
        screenwidth = init_window_name.winfo_screenwidth()
        screenheight = init_window_name.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        init_window_name.geometry(alignstr)
        # init_window_name["bg"] = "Navy"                                    #窗口背景色
        # init_window_name.attributes("-alpha",0.9)                          #虚化，值越小虚化程度越高
        row_count = 1

        # 选择文件解析
        self.file_title_label = Label(init_window_name, text='使用文件数据分析:', fg='red')
        self.file_title_label.grid(row=row_count, column=0, columnspan=2, sticky=W)

        row_count += 1
        self.file_path_label = Label(init_window_name, text='目标路径:')
        self.file_path_label.grid(row=row_count, column=0)
        self.file_path_Text = Entry(init_window_name, width=40)
        self.file_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_file_btn = Button(init_window_name, text="选择分析的文件", bg="lightblue",command=self.select_file_analysis)  # 调用内部方法  加()为直接调用
        self.select_file_btn.grid(row=row_count, column=3)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(init_window_name, text='日志')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(init_window_name, width=66, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=10)

    def select_file_analysis(self):
        '''
        选择文件分析
        :return:
        '''
        # 选择文件path_接收文件地址
        path_content = tkinter.filedialog.askopenfilenames()
        # 通过replace函数替换绝对文件地址中的/来使文件可被程序读取
        self.file_path_Text.delete(0, END)
        self.file_path_Text.insert(index=0, string=path_content)

        all_file_data = []
        missing_tick = []
        data_type = ''
        if path_content[0].find('.dat') > 0 or path_content[0].find('.hea') > 0:
            self.analysis_mit16_file(path_content[0])
            return

        # 读取文件数据
        read_file = ReadFile()
        for file_path_content in path_content:
            self.write_log_to_Text('解析文件:'+file_path_content)
            print(file_path_content)

            data_buffer,missing_data,type = read_file.read_file_data(file_path_content)
            if data_buffer is None or len(data_buffer) == 0:
                self.write_log_to_Text(file_path_content + '文件为空')
                continue
            data_type = type

            for file_dict in data_buffer:
                all_file_data.append(file_dict)
            for file_missing_dict in missing_data:
                missing_tick.append(file_missing_dict)


        all_file_data.sort(key=lambda f: f["recordTime"])
        drawing_view = DrawingView('')
        if data_type == 'ecg':
            drawing_view.draw_ECG_acc(all_file_data, missing_tick)
        elif data_type == 'temp':
            drawing_view.draw_temp(all_file_data)
        elif data_type == 'spo2':
            drawing_view.draw_SpO2(all_file_data)

    def analysis_mit16_file(self,file_path_name):
        read_file = ReadFile()
        all_data = read_file.read_mit16_data(file_path_name)
        drawing_view = DrawingView('')
        drawing_view.draw_ECG_acc(all_data,[])

    # 获取当前时间
    def get_current_time(self):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return current_time

    # 日志动态打印
    def write_log_to_Text(self, logmsg):
        global LOG_LINE_NUM
        current_time = self.get_current_time()
        logmsg_in = str(current_time) + " " + str(logmsg) + "\n"  # 换行
        if LOG_LINE_NUM <= 30:
            self.log_data_Text.insert(END, logmsg_in)
            LOG_LINE_NUM = LOG_LINE_NUM + 1
        else:
            self.log_data_Text.delete(1.0, 2.0)
            self.log_data_Text.insert(END, logmsg_in)


def gui_start():
    init_window = Tk()  # 实例化出一个父窗口
    ZMJ_PORTAL = MY_GUI()
    # 设置根窗口默认属性
    ZMJ_PORTAL.set_init_window(init_window)

    init_window.mainloop()  # 父窗口进入事件循环，可以理解为保持窗口运行，否则界面不展示


if __name__ == "__main__":
    # gui_start()
    readfile = ReadFile()
    all_data,miss,type = readfile.read_file_data('/Users/weixu/Documents/维灵/数据分析/滤波分析/newPat.txt')

    for dict in all_data:
        ecg_array = dict["ecg"]
        denoise_array = dict["denoiseEcg"]
        max_ecg_value = -100000
        min_ecg_value = -100000
        for ecg_value in ecg_array:
            if max_ecg_value == -100000:
                max_ecg_value = ecg_value
            if min_ecg_value == -100000:
                min_ecg_value = ecg_value

            if ecg_value > max_ecg_value:
                max_ecg_value = ecg_value
            if ecg_value < min_ecg_value:
                min_ecg_value = ecg_value

        max_denoiseEcg_value = -100000
        min_denoiseEcg_value = -100000
        for denoiseEcg_value in denoise_array:
            if max_denoiseEcg_value == -100000:
                max_denoiseEcg_value = denoiseEcg_value
            if min_denoiseEcg_value == -100000:
                min_denoiseEcg_value = denoiseEcg_value

            if denoiseEcg_value > max_denoiseEcg_value:
                max_denoiseEcg_value = denoiseEcg_value
            if denoiseEcg_value < min_denoiseEcg_value:
                min_denoiseEcg_value = denoiseEcg_value

        print(f"时间={dict['recordTime']}")
        print(f"max_ecg_value={max_ecg_value}\nmin_ecg_value={min_ecg_value}\nmax_denoiseEcg_value={max_denoiseEcg_value}\nmin_denoiseEcg_value={min_denoiseEcg_value}")
        print(f"ecg差值={max_ecg_value-min_ecg_value}   denoiseEcg差值={max_denoiseEcg_value-min_denoiseEcg_value}")
        rate = (max_denoiseEcg_value-min_denoiseEcg_value)/(max_ecg_value-min_ecg_value)
        print(f"rate={rate}")

