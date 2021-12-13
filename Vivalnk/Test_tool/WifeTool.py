#!/usr/bin/env python
# coding:utf-8

from tkinter import *
import tkinter.filedialog
import os
import time
import sys
import codecs

LOG_LINE_NUM = 0

class MY_GUI():

    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.download_data_UI()

        self.MsgFilePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'SaveExcelFile')
        print('save file path=' + self.MsgFilePath)

        # 如何文件夹不存在  直接创建  顺带创建三个文件
        if not os.path.exists(self.MsgFilePath):
            self.mkdir(self.MsgFilePath)

        write_path_name = os.path.join(self.MsgFilePath, '王小萍.csv')
        if not os.path.exists(write_path_name):
            f = codecs.open(write_path_name,'ab+','utf-8')
            info_msg = '淘宝Id,姓名,电话,地址\n'
            f.write(info_msg)
            f.close()


    # 创建文件夹
    def mkdir(self, dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
    # 从vCloud下载数据界面
    def download_data_UI(self):
        self.download_frame = Frame(self.init_window_name)
        self.download_frame.grid(row=20, column=10)

        row_count = 1
        self.cloud_title_label = Label(self.download_frame,
                                       text='将带有电话地址的信息拷入解析:',
                                       fg='red')
        self.cloud_title_label.grid(column=0, columnspan=4, sticky=W)
        # 导入下载的id和key
        self.input_secret_title = Label(self.download_frame, text='导入信息:', fg='black')
        self.input_secret_title.grid(row=row_count, column=0)
        self.input_path_Text = Entry(self.download_frame, width=60)
        self.input_path_Text.grid(row=row_count, column=1, columnspan=4, sticky=W)

        row_count += 1
        # 设备号
        self.sn_label = Label(self.download_frame, text='淘宝号:', fg='black')
        self.sn_label.grid(row=row_count, column=0)
        # self.sn_eg_label = Label(self.download_frame,
        #                          text='eg:ECGRec_202003/C800001,B33.00031731,O2 9930,BP5S_004D320D667F', fg='black')
        # self.sn_eg_label.grid(row=row_count, column=2, columnspan=4)
        sn_default_value = StringVar()
        sn_default_value.set('')
        self.sn_Text = Entry(self.download_frame, textvariable=sn_default_value,width=60)
        self.sn_Text.grid(row=row_count, column=1,)

        # row_count += 1
        # # 起始时间输入
        # self.init_data_label = Label(self.download_frame, text="Start Time:", fg='black')
        # self.init_data_label.grid(row=row_count, column=0)
        # st_default_value = StringVar()
        # st_default_value.set('')
        # self.init_data_Text = Entry(self.download_frame, textvariable=st_default_value)  # 开始时间
        # self.init_data_Text.grid(row=row_count, column=1)
        # self.time_eg_label = Label(self.download_frame, text="eg：2020-07-19 09:00:00", fg='black')
        # self.time_eg_label.grid(row=row_count, column=2)
        #
        # row_count += 1
        # # 结束时间输入
        # self.result_data_label = Label(self.download_frame, text="End Time:", fg='black')
        # self.result_data_label.grid(row=row_count, column=0)
        # et_default_value = StringVar()
        # et_default_value.set('')
        # self.result_data_Text = Entry(self.download_frame, textvariable=et_default_value)  # 结束时间
        # self.result_data_Text.grid(row=row_count, column=1)
        #
        # row_count += 1
        # # 下载文件夹地址
        # self.download_title = Label(self.download_frame, text='Storage directory:', fg='black')
        # self.download_title.grid(row=row_count, column=0)
        # self.download_path_Text = Entry(self.download_frame, width=40)
        # self.download_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        # self.select_dl_btn = Button(self.download_frame, text="Select the storage directory", bg="lightblue",
        #                             command=self.select_dl_filefolder, fg='black')  # 调用内部方法  加()为直接调用
        # self.select_dl_btn.grid(row=row_count, column=3)

        row_count += 1
        # 开始下载解析
        self.start_download_ana_button = Button(self.download_frame, text="解析存储到excel", fg="red",
                                                command=self.start_cloud_analysis)  # 调用内部方法  加()为直接调用
        self.start_download_ana_button.grid(row=row_count, column=1, columnspan=2)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(self.download_frame, text='Log:', fg='black')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.download_frame, width=90, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=13)

    def get_file_idAndKey(self):
        pass

    def select_dl_filefolder(self):
        pass


    def start_cloud_analysis(self):
        info = self.input_path_Text.get()

        info_array = []
        if info.find('，') >= 0:
            info_array = info.split('，')
        elif info.find(',') >= 0:
            info_array = info.split(',')

        if len(info_array) == 0:
            return
        if info_array[0] == '':
            return

        taobao_id = self.sn_Text.get()

        if taobao_id == '':
            return
        write_path_name = os.path.join(self.MsgFilePath,'王小萍.csv')
        f = codecs.open(write_path_name, 'ab+', 'utf-8')
        write_value = taobao_id + ',' + info_array[0] + ',' + info_array[1] + ',' + info_array[2] + '\n'
        f.write(write_value)
        f.close()
        self.write_log_to_Text(write_value)
        self.write_log_to_Text('存储成功')

    # 获取当前时间
    def get_current_time(self):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return current_time

    # 日志动态打印
    def write_log_to_Text(self, logmsg):
        global LOG_LINE_NUM
        current_time = self.get_current_time()
        logmsg_in = str(current_time) + " " + str(logmsg) + "\n"  # 换行
        if LOG_LINE_NUM <= 1000:
            self.log_data_Text.insert(END, logmsg_in)
            LOG_LINE_NUM = LOG_LINE_NUM + 1
        else:
            self.log_data_Text.delete(1.0, 2.0)
            self.log_data_Text.insert(END, logmsg_in)

        self.log_data_Text.see(tkinter.END)
        self.log_data_Text.update()

def gui_start():
    root = Tk()
    root.title("Wife DataTool")  # 窗口名
    width = 900
    height = 700
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    root.geometry(alignstr)

    #  创建一个顶级菜单
    menubar = Menu(root)

    my_app = MY_GUI(root)

    #  显示菜单
    root.config(menu=menubar)
    # root.bind_all("<Control-N>", lambda event: my_app.splicy_multi_device_log_UI())
    mainloop()



if __name__ == "__main__":
    gui_start()