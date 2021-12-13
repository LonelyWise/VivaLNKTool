#!/usr/bin/env python
# coding:utf-8
"""
1.直接下载ECG、Temp和SpO2数据画图工具
2.选择文件画图工具
"""
import time
import datetime
from tkinter import *
import tkinter.filedialog
from tkinter.messagebox import showinfo, showerror
from PIL import Image, ImageTk
import sys
import os
import json
import os.path as osp
from enum import Enum
import threading
import platform
import configparser
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
# 保证ScriptTool_analysis模块导入不会报错   错误内容：ModuleNotFoundError: No module named 'ScriptTool_analysis'
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from ScriptTool_analysis.VivaLNK_Unity import ToolClass
from ScriptTool_analysis.VivaLNK_Drawing import DrawingView
from ScriptTool_analysis.VivaLNK_OnlyDownloadECG import download_ecg_data
from ScriptTool_analysis.VivaLNK_Reading import ReadFile
from ScriptTool_analysis.VivaLNK_TempAPP import DownloadTemp
from ScriptTool_analysis.VivaLNK_SecretDownload import SecretDownload  # 新增的带有token秘钥的请求
from ScriptTool_analysis.VivaLNK_ProcessMedicalFile import ProcessISHNE,ProcessMitData # 生成ishne文件和读取

from ScriptTool_analysis.VivaLNK_NBTransformMit import NalongDataAnalysis
from ScriptTool_analysis.VivaLNK_SplicyLog import MultiDeviceSplicyLog
from ScriptTool_analysis.ACC_check_bp import caculate_acc_quality
from ScriptTool_analysis.ACC_NoiseUnitTest import TestACC

from ScriptTool_analysis.VivaLNK_Dialog import MyDialog
from ScriptTool_analysis.VivaLNK_Dialog import SelectDrawFrame
LOG_LINE_NUM = 0

class DestroyFrame(Enum):
    default = 1
    download = 2
    analysis = 3
    mit = 4
    ishne = 5
    download_tempServer = 6
    splicy_device_log = 7
    nb_to_mit = 8
    plot_coparison = 9

class MY_GUI():
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.id_value = ''
        self.key_value = ''
        self.token_value = ''
        self.deviceName = ''
        self.startTime = ''
        self.endTime = ''
        self.download_path = '/data'
        self.auth_path = "/auth"
        self.download_host = 'https://vcloud2.vivalnk.com'
        self.MsgFilePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),'MsgFile')
        print('save file path=' + self.MsgFilePath)
        self.img_png = None

        self.iniPath = os.path.join(self.MsgFilePath, 'AppConfig.ini')
        # 如何文件夹不存在  直接创建  顺带创建三个文件
        if not os.path.exists(self.MsgFilePath):
            self.mkdir(self.MsgFilePath)

        config = configparser.ConfigParser()
        if not os.path.exists(self.iniPath):
            config['Download.config'] = {}
            config['Download.config']['deviceName'] = ""
            config['Download.config']['startTime'] = ""
            config['Download.config']['endTime'] = ""

            config['Download.config']['id'] = "e60da7973ce6498e8cfd12c6c"
            config['Download.config']['secret'] = "FpSTHLk[5nR``W8djjc8u7M4X8y^lyfkLEx8D<LX"
            config['Download.config']['token'] = ""

            config['Download.config']['production'] = 'YES'
            config['Download.config']['host production'] = 'https://vcloud2.vivalnk.com'
            config['Download.config']['host test'] = 'https://vcloud-test.vivalnk.com'
            config['Download.config']['data path'] = '/data'
            config['Download.config']['auth path'] = "/auth"

            with open(self.iniPath, 'w') as configfile:
                config.write(configfile)
        else:
            config.read(self.iniPath)
            download_config = config['Download.config']
            self.id_value = download_config['id']
            self.key_value = download_config['secret']
            self.token_value = download_config['token']
            self.deviceName = download_config['deviceName']
            self.startTime = download_config['startTime']
            self.endTime = download_config['endTime']
            production = download_config['production']
            self.download_host = download_config['host production']
            if production != 'YES':
                self.download_host = download_config['host test']
            self.download_path = download_config['data path']
            if 'auth path' in download_config:
                self.auth_path = download_config["auth path"]
            else:
                config.set('Download.config', 'auth path', self.auth_path)
                with open(self.iniPath, 'w') as configfile:
                    config.write(configfile)

        self.get_frame_value = 0
        self.file_path_array = []
        # 加载默认的UI
        self.default_UI()

    def default_UI(self):
        self.default_frame = Frame(self.init_window_name)
        self.default_frame.grid(row=20, column=10)
        self.get_frame_value = DestroyFrame.default.value

        image_path = os.path.join(self.MsgFilePath, 'company_logo.png')
        if os.path.exists(image_path):
            img_open = Image.open(image_path)
            self.img_png = ImageTk.PhotoImage(img_open)
            label_img = Label(self.default_frame, image=self.img_png)
            label_img.pack()

        label1 = Label(self.default_frame, text='1.Software name: VivaLNK DataTool\n', fg='black', height=1, width=100, anchor=NW)
        label1.pack()

        label2_title = Label(self.default_frame, text='2.Objective\n', fg='black', height=1, width=100, anchor=NW)
        label2_title.pack()

        label2_one = Label(self.default_frame, text='  To download the raw data from Vivalink Cloud (i.e., vCloud) uploading by Vivalink sensors,including ECG data,three accelerometer data, \n', fg='black', height=1, width=100, anchor=NW)
        label2_one.pack()

        label2_two = Label(self.default_frame, text='and multi vital signs.The tool also can provide the data integrity analysis and other functions.The sensors can connect to the SDK Demo APP\n', fg='black', height=1, width=100, anchor=NW)
        label2_two.pack()

        label2_three = Label(self.default_frame, text=' (provided in SDK release package) and other mobile APPs (on app stores) by Bluetooth,and the raw data will upload to vCloud.\n', fg='black', height=1, width=100, anchor=NW)
        label2_three.pack()

        label3_title = Label(self.default_frame, text='3.Function Support\n', fg='black', height=1, width=100, anchor=NW)
        label3_title.pack()

        label3_one = Label(self.default_frame, text='  1) Vivalink sensor data file download.\n', fg='black', height=1, width=100, anchor=NW)
        label3_one.pack()

        label3_two = Label(self.default_frame, text='  2) To convert ECG format between JSON, MIT 16, ISHNE, NB etc.\n', fg='black', height=1, width=100, anchor=NW)
        label3_two.pack()

        label3_three = Label(self.default_frame, text='  3)To draw ECG and ACC waveform.\n', fg='black', height=1, width=100, anchor=NW)
        label3_three.pack()

        label3_four = Label(self.default_frame, text='  4)Support multi-device data log separation.\n', fg='black', height=1, width=100, anchor=NW)
        label3_four.pack()

        label4_title = Label(self.default_frame, text='4.Environmental Support\n', fg='black', height=1, width=100, anchor=NW)
        label4_title.pack()

        label4_one = Label(self.default_frame, text='  Support to run on windows. Provide the “.exe” file to run directly by double-click need to install.\n',fg='black',height=1,width=100,anchor=NW)
        label4_one.pack()

        label4_two = Label(self.default_frame, text='vCloud data file download requires a specific ID and KEY, this file already included in release package with “.exe” file. \n', fg='black', height=1, width=100, anchor=NW)
        label4_two.pack()

    # 从vCloud下载数据界面
    def download_data_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.download.value

        self.download_frame = Frame(self.init_window_name)
        self.download_frame.grid(row=20, column=10)

        row_count = 1
        cloud_title_label = Label(self.download_frame, text='The input conditions for downloading data from the cloud are as follows (ECG/Temp/SpO2/BP):', fg='red')
        cloud_title_label.grid(column=0, columnspan=4, sticky=W)
        # 导入下载的id和key
        input_secret_title = Label(self.download_frame, text='Import key:', fg='black')
        input_secret_title.grid(row=row_count, column=0)
        self.input_path_Text = Entry(self.download_frame, width=40)
        self.input_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)

        if self.id_value != '' and self.key_value != '':
            insert_line = 'id:'+self.id_value+'  ' + 'secret:'+self.key_value
            self.input_path_Text.insert(index=0, string=insert_line)
        select_input_secret_btn = Button(self.download_frame, text="Select a document(Provided by VivaLNK)", bg="lightblue", command=self.get_file_idAndKey, fg='black')  # 调用内部方法  加()为直接调用
        select_input_secret_btn.grid(row=row_count, column=3)

        row_count += 1
        # 设备号
        device_sn_label = Label(self.download_frame, text='device Lot/SN:', fg='black')
        device_sn_label.grid(row=row_count, column=0)
        device_sn_eg_label = Label(self.download_frame, text='eg:ECGRec_202003/C800001,B33.00031731,O2 9930,BP5S_004D320D667F', fg='black')
        device_sn_eg_label.grid(row=row_count, column=2, columnspan=4)
        sn_default_value = StringVar()
        sn_default_value.set(self.deviceName)
        self.sn_Text = Entry(self.download_frame, textvariable=sn_default_value)
        self.sn_Text.grid(row=row_count, column=1)

        row_count += 1
        # 起始时间输入
        self.init_data_label = Label(self.download_frame, text="Start Time:", fg='black')
        self.init_data_label.grid(row=row_count, column=0)
        st_default_value = StringVar()
        st_default_value.set(self.startTime)
        self.init_data_Text = Entry(self.download_frame, textvariable=st_default_value)  # 开始时间
        self.init_data_Text.grid(row=row_count, column=1)
        self.time_eg_label = Label(self.download_frame, text="eg：2020-07-19 09:00:00", fg='black')
        self.time_eg_label.grid(row=row_count, column=2)

        row_count += 1
        # 结束时间输入
        self.result_data_label = Label(self.download_frame, text="End Time:",fg='black')
        self.result_data_label.grid(row=row_count, column=0)
        et_default_value = StringVar()
        et_default_value.set(self.endTime)
        self.result_data_Text = Entry(self.download_frame, textvariable=et_default_value)  # 结束时间
        self.result_data_Text.grid(row=row_count, column=1)

        row_count += 1
        # 下载文件夹地址
        self.download_title = Label(self.download_frame, text='Storage directory:',fg='black')
        self.download_title.grid(row=row_count, column=0)
        self.download_path_Text = Entry(self.download_frame, width=40)
        self.download_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_dl_btn = Button(self.download_frame, text="Select the storage directory", bg="lightblue",
                                    command=self.select_dl_filefolder,fg='black')  # 调用内部方法  加()为直接调用
        self.select_dl_btn.grid(row=row_count, column=3)

        row_count += 1
        # 开始下载解析
        self.start_download_ana_button = Button(self.download_frame, text="Start downloading analysis", fg="red",
                                                command=self.start_cloud_analysis)  # 调用内部方法  加()为直接调用
        self.start_download_ana_button.grid(row=row_count, column=1, columnspan=2)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(self.download_frame, text='Log:',fg='black')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.download_frame, width=90, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=13)
    # 功能函数
    def start_cloud_analysis(self):
        tq = threading.Thread(target=self.download_data_from_vCloud, name='vCloud', args=())
        tq.start()
    def download_data_from_vCloud(self):
        if self.id_value == '' or self.key_value == '':
            showerror(title='Error', message = 'No key has been imported, please import the key information provided from VivaLNK first.')
            return

        sn_str = self.sn_Text.get()
        start_time_str = self.init_data_Text.get()
        end_time_str = self.result_data_Text.get()

        if start_time_str.find('-') < 0 or start_time_str.find(':') < 0 or start_time_str.find(' ') < 0:
            self.write_log_to_Text('Incorrect start time format')
            return
        if end_time_str.find('-') < 0 or end_time_str.find(':') < 0 or end_time_str.find(' ') < 0:
            self.write_log_to_Text('End time format error')
            return
        start_time_value = time.mktime(
            datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").timetuple()) * 1000
        end_time_value = time.mktime(
            datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S").timetuple()) * 1000
        if end_time_value < start_time_value:
            self.write_log_to_Text('End time is less than start time')

        if sn_str.find('.') != 3 and sn_str.find('ECGRec_') != 0 and sn_str.find('O2') != 0 and sn_str.find('BP5') != 0:
            return self.write_log_to_Text('The format of the device number is wrong and does not fit the download!!!')

        device_type = ''
        # isalpha()检查所有字符都是字母
        if sn_str[0].isalpha() and sn_str.find('.') > 0:
            if len(sn_str) != 12:
                self.write_log_to_Text('The length of the entered body temperature device number is wrong')
                return
            device_type = 'Temp'
            self.write_log_to_Text('Start downloading body temperature data')
            # download_universal = DownloadDataFromVCloud(self.download_path_Text.get(), app_id=app_id_str,
            #                                             Universal_log=self.write_log_to_Text)
            # json_universal = download_universal.input_download_param(sn_str, int(start_time_value),
            #                                                          int(end_time_value))
        elif sn_str[0].isalpha() and sn_str.find('O2') == 0:
            if len(sn_str) != 7:
                self.write_log_to_Text('The length of the input blood oxygen device number is wrong')
                return
            device_type = 'SpO2'
            self.write_log_to_Text('Start downloading blood oxygen saturation data')
            # download_universal = DownloadDataFromVCloud(self.download_path_Text.get(), app_id=app_id_str,
            #                                             Universal_log=self.write_log_to_Text)
            # json_universal = download_universal.input_download_param(sn_str, int(start_time_value),
            #                                                          int(end_time_value))
        elif sn_str.find('BP5') == 0:
            device_type = 'BP'
            self.write_log_to_Text('Start downloading blood pressure data')
            # download_universal = DownloadDataFromVCloud(self.download_path_Text.get(), app_id=app_id_str,
            #                                             Universal_log=self.write_log_to_Text)
            # json_universal = download_universal.input_download_param(sn_str, int(start_time_value),
            #                                                          int(end_time_value))
        elif sn_str.find('ECGRec_') >= 0:
            device_type = 'ECG'
            self.write_log_to_Text('Start downloading ECG data')
            if len(sn_str) != 21:
                self.write_log_to_Text('The length of the entered device number is wrong')
                return
            # download_data = download_ecg_data(self.download_path_Text.get(), app_id=app_id_str,
            #                                   Print_log=self.write_log_to_Text)
            # all_data, missing_tick = download_data.download(sn_str, int(start_time_value), int(end_time_value))

        config = configparser.ConfigParser()
        config.read(self.iniPath)
        config.set("Download.config",'deviceName',sn_str)
        config.set("Download.config",'startTime',start_time_str)
        config.set("Download.config", 'endTime', end_time_str)
        with open(self.iniPath,'w') as configFile:
            config.write(configFile)

        secret_download = SecretDownload(self.download_path_Text.get(),Download_Log=self.write_log_to_Text,secret_id_value=self.id_value,secret_key_value=self.key_value)
        secret_download.download_token = self.token_value
        secret_download.download_path = self.download_path
        secret_download.download_host = self.download_host
        secret_download.auth_path = self.auth_path
        all_data,missing_tick = secret_download.before_download_cut_time(device_type,sn_str,int(start_time_value),int(end_time_value))
        if len(all_data) == 0:
            return

        if device_type == 'ECG':
            self.write_log_to_Text('generating MIT16 files, please wait a moment')
            if len(missing_tick) != 0:
                compensatory_Array = []
                array_count = 128
                while array_count > 0:
                    compensatory_Array.append(8700)
                    array_count -= 1

                for miss_tuple in missing_tick:
                    st = int(miss_tuple[0]) + 1000
                    et = int(miss_tuple[1])
                    while st < et:
                        miss_dict = {}
                        miss_dict['ecg'] = compensatory_Array
                        miss_dict['recordTime'] = st
                        miss_dict['flash'] = 1
                        all_data.append(miss_dict)
                        st += 1000
                # 补数据后排序一下
                all_data.sort(key=lambda f: f["recordTime"])

            ecg_buffer = []
            mit16_start_time = 0
            for dict in all_data:
                if mit16_start_time == 0:
                    mit16_start_time = dict['recordTime']
                ecg_array = dict['ecg']
                for ecg_value in ecg_array:
                    ecg_buffer.append(ecg_value)

            ecg_all = []
            ecg_all.append(ecg_buffer)

            mit_path = os.path.join(self.download_path_Text.get(),'mit16')
            if not os.path.exists(mit_path):
                os.makedirs(mit_path, exist_ok=True)

            process_mit = ProcessMitData(mit_log=self.write_log_to_Text)
            process_mit.generate_mit_file('VivaLNK' + '-' + str(mit16_start_time), 128, [1000], ecg_all,
                                          mit16_start_time, None, mit_path)

    def get_file_idAndKey(self):
        file_name = tkinter.filedialog.askopenfilename()
        with open(file_name,'r') as file_to_read:
            while True:
                line = file_to_read.readline()
                if line:
                    secret_json = json.loads(line)
                    if ('id' in secret_json) and ('key' in secret_json):
                        self.id_value = secret_json['id']
                        self.key_value = secret_json['key']
                        self.input_path_Text.insert(index=0,string=f'id:{self.id_value},key:{self.key_value}')
                        self.write_log_to_Text('Input Success')
                    else:
                        self.write_log_to_Text('file content error')
                else:
                    break
        # 导入新的ID和secret还有修改配置
        config = configparser.ConfigParser()
        config.read(self.iniPath)
        config.set('Download.config', 'token', '')
        config.set('Download.config', 'id', self.id_value)
        config.set('Download.config', 'secret', self.key_value)
        with open(self.iniPath, 'w') as configfile:
            config.write(configfile)

    # 选择下载数据存储的地址
    def select_dl_filefolder(self):
        '''
        选择下载数据存储的地址
        :return:
        '''
        filefoler_path = tkinter.filedialog.askdirectory()
        print(filefoler_path)
        # self.download_path_Text.select_clear()
        self.download_path_Text.delete(0, END)
        self.download_path_Text.insert(index=0, string=filefoler_path)

    # 选择文件分析绘图界面
    def file_analysis_lost_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.analysis.value

        self.analysis_frame = Frame(self.init_window_name)
        self.analysis_frame.grid(row=10,column=10)
        row_count = 1
        self.analysis_date_note_label = Label(self.analysis_frame,text='The data of mit16 file and ISHNE file will directly draw the waveform', fg='black')
        self.analysis_date_note_label.grid(row=row_count,column=0,columnspan=4, sticky=W)
        row_count += 1
        # 选择文件解析
        self.file_title_label = Label(self.analysis_frame, text='Use file data to analyze data integrity (data downloaded from the cloud, mobile phone log data, etc.):', fg='red')
        self.file_title_label.grid(row=row_count, column=0, columnspan=4, sticky=W)

        row_count += 1
        self.wave_label = Label(self.analysis_frame, text='Draw waveform:',fg='black')
        self.wave_label.grid(row=row_count, column=0)
        self.var_wave_true = BooleanVar()
        self.select_wave_btn = Checkbutton(self.analysis_frame, text='YES', variable=self.var_wave_true,fg='black')
        self.select_wave_btn.grid(row=row_count, column=1)

        row_count += 1
        merge_label = Label(self.analysis_frame, text='Merge into one file:', fg='black')
        merge_label.grid(row=row_count, column=0)
        self.var_merge_true = BooleanVar()
        self.select_merge_btn = Checkbutton(self.analysis_frame, text='YES', variable=self.var_merge_true, fg='black')
        self.select_merge_btn.grid(row=row_count, column=1)

        row_count += 1
        SNR_label = Label(self.analysis_frame, text='denoise ECG waveform:', fg='black')
        SNR_label.grid(row=row_count, column=0)
        self.var_SNR_true = BooleanVar()
        self.select_SNR_btn = Checkbutton(self.analysis_frame, text='YES', variable=self.var_SNR_true,fg='black')
        self.select_SNR_btn.grid(row=row_count, column=1)

        row_count += 1
        self.file_path_label = Label(self.analysis_frame, text='File directory path:',fg='black')
        self.file_path_label.grid(row=row_count, column=0)
        self.file_path_Text = Entry(self.analysis_frame, width=40)
        self.file_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_file_btn = Button(self.analysis_frame, text="Select the file to analyze", bg="lightblue",
                                      command=self.select_file_analysis,fg='black')  # 调用内部方法  加()为直接调用
        self.select_file_btn.grid(row=row_count, column=3)

        row_count += 1
        # 开始下载解析
        self.start_analysis_btn = Button(self.analysis_frame, text="Start analysis", fg="red",
                                                command=self.start_file_analysis)  # 调用内部方法  加()为直接调用
        self.start_analysis_btn.grid(row=row_count, column=1, columnspan=2)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(self.analysis_frame, text='Log:',fg='black')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.analysis_frame, width=90, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=1, columnspan=13)
    # 获取文件路径
    def select_file_analysis(self):
        '''选择文件分析
        :return:
        '''
        # 选择接收文件地址
        self.file_path_array = tkinter.filedialog.askopenfilenames()
        self.file_path_Text.delete(0, END)# 删除之前输入框的内容
        self.file_path_Text.insert(index=0, string=self.file_path_array)# 插入新选择的文件
    # 开始分析
    def start_file_analysis(self):
        if len(self.file_path_array) == 0:
            self.write_log_to_Text('Please select the file to analyze！！！')

        # mit16文件格式
        if self.file_path_array[0].find('.dat') > 0 or self.file_path_array[0].find('.hea') > 0:
            self.analysis_mit16_file(self.file_path_array[0])
            return
        # nb文件格式
        if self.file_path_array[0].find('.nb') > 0:
            self.write_log_to_Text('nb文件暂时不支持分析')
            nb_file_name = self.file_path_array[0]
            tooClass = ToolClass()
            dir_name = tooClass.get_current_file_directory(nb_file_name)

            start_time_str = "2021-05-11 09:00:00"
            start_time_value = time.mktime(
                datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").timetuple()) * 1000

            # read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
            # read_file.read_nb_file_content(nb_file_name)

            nalong = NalongDataAnalysis(dir_name,nalong_log=self.write_log_to_Text,mit_start_time=int(start_time_value))
            nalong.read_nb_file_content(nb_file_name)

            return

        # ishne文件格式
        if self.file_path_array[0].find('.ecg') > 0:
            process_ishne = ProcessISHNE(ishne_log=self.write_log_to_Text)
            all_data = process_ishne.read_iSHNE_data(self.file_path_array[0])
            drawing_view = DrawingView('', Draw_log=self.write_log_to_Text)
            drawing_view.draw_mit_ishne(all_data)
            return

        # 读取所有文件数据
        read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
        all_file_data, missing_tick, data_type = read_file.read_batch_files_data(batch_files_array=self.file_path_array,
                                                                                 compensatory_value=-1)

        if len(missing_tick) == 0:
            self.write_log_to_Text('No data is lost')

        # 判断是否需要绘制图形
        select_draw_wave = self.var_wave_true.get()
        # 判断是否需要合并至一个文件
        merge_file = self.var_merge_true.get()
        # 判断是否需要计算SNR
        denoise = self.var_SNR_true.get()

        print(f'{select_draw_wave},{merge_file},{denoise}')

        # if cal_SNR:
        # caculate_acc_quality(self.file_path_array)


        tooClass = ToolClass()
        if merge_file:
            # 合并数据到一个文件中
            read_file_name = self.file_path_array[0]
            dir_name = tooClass.get_current_file_directory(read_file_name)
            write_file_name = os.path.join(dir_name, 'allComplete.log')  # 拼装完整的文件路径
            tooClass.write_data_to_file(write_file_name, all_file_data)

        if select_draw_wave:
            drawing_view = DrawingView('', Draw_log=self.write_log_to_Text)
            if data_type == 'ecg':
                parameter = self.ask_select_parameter(SelectDrawFrame.default.value)
                if parameter is None:
                    self.write_log_to_Text("Did not choose the parameter you want to draw")
                    return
                drawing_view.draw_parameter = parameter
                if denoise:
                    drawing_view.denoise_waveform = True
                drawing_view.draw_waveform(all_file_data, missing_tick)
            elif data_type == 'temp':
                drawing_view.draw_temp(all_file_data)
            elif data_type == 'spo2':
                drawing_view.draw_SpO2(all_file_data)
            elif data_type == 'bp':
                drawing_view.draw_BP2(all_file_data)

        self.file_path_array = []

    def plot_comparison(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.plot_coparison.value

        self.plot_comparison_frame = Frame(self.init_window_name)
        self.plot_comparison_frame.grid(row=10, column=10)
        row_count = 1

        # 选择文件解析
        self.comparison_title_label = Label(self.plot_comparison_frame,
                                      text='Select the files that need drawing comparison:',
                                      fg='red')
        self.comparison_title_label.grid(row=row_count, column=0, columnspan=4, sticky=W)

        row_count += 1
        comparison_path_label1 = Label(self.plot_comparison_frame, text='Comparison File path 1:', fg='black')
        comparison_path_label1.grid(row=row_count, column=0)
        self.comparison_path_Text1 = Entry(self.plot_comparison_frame, width=40)
        self.comparison_path_Text1.grid(row=row_count, column=1, columnspan=2, sticky=W)
        comparison_select_file_btn1 = Button(self.plot_comparison_frame,
                                                 text="Select the file to drawing",
                                                 bg="lightblue",
                                                 command=self.select_comparison_file1,
                                                 fg='black')  # 调用内部方法  加()为直接调用
        comparison_select_file_btn1.grid(row=row_count, column=3)

        row_count += 1
        comparison_path_label2 = Label(self.plot_comparison_frame, text='Comparison File path 2:', fg='black')
        comparison_path_label2.grid(row=row_count, column=0)
        self.comparison_path_Text2 = Entry(self.plot_comparison_frame, width=40)
        self.comparison_path_Text2.grid(row=row_count, column=1, columnspan=2, sticky=W)
        comparison_select_file_btn2 = Button(self.plot_comparison_frame,
                                                 text="Select the file to drawing",
                                                 bg="lightblue",
                                                 command=self.select_comparison_file2,
                                                 fg='black')  # 调用内部方法  加()为直接调用
        comparison_select_file_btn2.grid(row=row_count, column=3)

        row_count += 1
        # 开始下载解析
        self.comparison_start_analysis_btn = Button(self.plot_comparison_frame, text="Start comparison", fg="red",
                                         command=self.start_file_comparison)  # 调用内部方法  加()为直接调用
        self.comparison_start_analysis_btn.grid(row=row_count, column=1, columnspan=2)

        row_count += 1
        # 日志打印功能
        self.comparison_log_label = Label(self.plot_comparison_frame, text='Log:', fg='black')
        self.comparison_log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.plot_comparison_frame, width=90, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=1, columnspan=13)

    def select_comparison_file1(self):
        '''
        开始选择对比文件  并获取地址
        '''
        self.comparison_file_path1 = tkinter.filedialog.askopenfilename()
        self.write_log_to_Text(self.comparison_file_path1)
        self.comparison_path_Text1.delete(0, END)  # 删除之前输入框的内容
        self.comparison_path_Text1.insert(index=0, string=self.comparison_file_path1)  # 插入新选择的文件

    def select_comparison_file2(self):
        '''
        开始选择对比文件  并获取地址
        '''
        self.comparison_file_path2 = tkinter.filedialog.askopenfilename()
        self.write_log_to_Text(self.comparison_file_path2)
        self.comparison_path_Text2.delete(0, END)  # 删除之前输入框的内容
        self.comparison_path_Text2.insert(index=0, string=self.comparison_file_path2)  # 插入新选择的文件

    def start_file_comparison(self):
        read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
        path1_data, path1_miss,path_type1 = read_file.read_batch_files_data(batch_files_array=[self.comparison_file_path1],compensatory_value=8700)

        read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
        path2_data, path2_miss, path_type2 = read_file.read_batch_files_data(
            batch_files_array=[self.comparison_file_path2], compensatory_value=8700)
        if path_type1 != path_type2:
            self.write_log_to_Text("The formats of the two files are not the same, so it is impossible to draw and analyze")
            return

        if len(path1_data) == 0 or len(path2_data) == 0:
            self.write_log_to_Text("There is an empty file in the comparison file")
            return

        parameter = self.ask_select_parameter(SelectDrawFrame.comparison.value)
        if parameter is None:
            self.write_log_to_Text("Did not choose the parameter you want to draw")
            return

        tool_class = ToolClass()
        file_name1 = tool_class.get_current_file_name(self.comparison_file_path1)
        file_name2 = tool_class.get_current_file_name(self.comparison_file_path2)

        draw = DrawingView(write_path='', Draw_log=self.write_log_to_Text)
        draw.draw_parameter = parameter
        draw.file_name1 = file_name1
        draw.file_name2 = file_name2
        draw.draw_comparison_waveform(path1_data, path2_data, path_type1)

    # 弹窗
    def ask_select_parameter(self, type):
        input_dialog = MyDialog(type=type)
        self.init_window_name.wait_window(input_dialog)  # 这一句很重要！！！
        response = input_dialog.paramter
        print(response)
        if response is None:
            return
        return response

    # json格式转mit16的界面
    def format_json_mit_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.mit.value

        self.fromat_json_frame = Frame(self.init_window_name)
        self.fromat_json_frame.grid(row=10, column=10)

        row_count = 1
        # 选择文件解析
        self.file_title_label = Label(self.fromat_json_frame, text="Select the file that needs to be converted into mit16 format data (data downloaded from the cloud, mobile phone log data, etc.):", fg='red')
        self.file_title_label.grid(row=row_count, column=0, columnspan=4, sticky=W)

        row_count += 1
        self.file_path_label = Label(self.fromat_json_frame, text='File directory path:',fg='black')
        self.file_path_label.grid(row=row_count, column=0)
        self.file_path_Text = Entry(self.fromat_json_frame, width=40)
        self.file_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_file_btn = Button(self.fromat_json_frame, text="Choose file conversion", bg="lightblue",
                                      command=self.transform_json_to_mit,fg='black')  # 调用内部方法  加()为直接调用
        self.select_file_btn.grid(row=row_count, column=3)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(self.fromat_json_frame, text='Log',fg='black')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.fromat_json_frame, width=66, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=10)
    # json转换为mit16格式的数据
    def transform_json_to_mit(self):
        compensatory_value = 8700
        # zero_value = self.var_wave_true.get()
        # threshold_value = self.var_wave_false.get()
        # if zero_value and threshold_value:
        #     self.write_log_to_Text('不允许选择两个补偿值')
        #     return
        # if zero_value:
        #     compensatory_value = 0
        # if threshold_value:
        #     compensatory_value = 8700

        # 选择文件path_接收文件地址
        json_file_path_array = tkinter.filedialog.askopenfilenames()
        # 通过replace函数替换绝对文件地址中的/来使文件可被程序读取
        self.file_path_Text.delete(0, END)
        self.file_path_Text.insert(index=0, string=json_file_path_array)

        # 读取文件数据
        read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
        all_file_data,missing_tick,data_type = read_file.read_batch_files_data(json_file_path_array,compensatory_value)

        # 获取文件夹路径
        tooClass = ToolClass()
        file_name = json_file_path_array[0]
        dir_name = tooClass.get_current_file_directory(file_name)

        if data_type == 'ecg':
            ecg_buffer = []
            mit16_start_time = 0
            for dict in all_file_data:
                if mit16_start_time == 0:
                    mit16_start_time = dict['recordTime']
                ecg_array = dict['ecg']
                for ecg_value in ecg_array:
                    ecg_buffer.append(ecg_value)

            ecg_all = []
            ecg_all.append(ecg_buffer)
            write_dir = dir_name + 'mit16'
            self.mkdir(write_dir)

            process_mit = ProcessMitData(mit_log=self.write_log_to_Text)
            process_mit.generate_mit_file('VivaLNK' + '-' + str(mit16_start_time), 128, [1000], ecg_all, mit16_start_time, None, dir_name + 'mit16/')
        else:
            self.write_log_to_Text('不是ECG数据无法转换成MIT16')

    # json格式转换ishne的UI界面
    def format_json_ishne_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.ishne.value

        self.fromat_ishne_frame = Frame(self.init_window_name)
        self.fromat_ishne_frame.grid(row=10, column=10)

        row_count = 1
        # 选择文件解析
        self.ishne_title_label = Label(self.fromat_ishne_frame, text='Select the files that need to be converted into ISHNE format data (data downloaded from the cloud, mobile phone log data, etc.):', fg='red')
        self.ishne_title_label.grid(row=row_count, column=0, columnspan=4, sticky=W)

        row_count += 1
        self.ishne_path_label = Label(self.fromat_ishne_frame, text='File directory path:', fg='black')
        self.ishne_path_label.grid(row=row_count, column=0)
        self.ishne_path_Text = Entry(self.fromat_ishne_frame, width=40)
        self.ishne_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_ishne_btn = Button(self.fromat_ishne_frame, text="Choose file conversion", bg="lightblue",
                                      command=self.transform_json_to_ishne, fg='black')  # 调用内部方法  加()为直接调用
        self.select_ishne_btn.grid(row=row_count, column=3)

        row_count += 1
        # 日志打印功能
        self.ishne_log_label = Label(self.fromat_ishne_frame, text='Log', fg='black')
        self.ishne_log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.fromat_ishne_frame, width=66, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=10)
    # json转换为ishne的数据
    def transform_json_to_ishne(self):
        # 选择文件path_接收文件地址
        ishne_paths_array = tkinter.filedialog.askopenfilenames()
        self.ishne_path_Text.delete(0,END)
        self.ishne_path_Text.insert(index=0, string=ishne_paths_array)

        # 读取文件数据
        read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
        all_file_data,miss_tick,data_type = read_file.read_batch_files_data(ishne_paths_array,compensatory_value=-1)

        all_file_data.sort(key=lambda f: f["recordTime"])
        start_time = all_file_data[0]['recordTime']

        # 获取文件夹路径
        tooClass = ToolClass()
        file_name = ishne_paths_array[0]
        dir_name = tooClass.get_current_file_directory(file_name=file_name)

        self.mkdir(dir_name+'ishne')
        ishne_dir_file_name = dir_name+'ishne/'+str(start_time)+'.ecg'
        all_ecg_data = []
        for json_dict in all_file_data:
            ecg_array = json_dict['ecg']
            for ecg_value in ecg_array:
                ecg_float_value = ecg_value / 1000.0
                all_ecg_data.append(ecg_float_value)

        if data_type == 'ecg':
            process_ishne = ProcessISHNE(ishne_log=self.write_log_to_Text)
            process_ishne.generate_ishne_format_file(ecg_data_list=all_ecg_data,first_time=start_time,output_file_path=ishne_dir_file_name)
        else:
            self.write_log_to_Text('Non-ECG data file')

    # nb文件格式转换为mit16
    def format_nb_mit_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.nb_to_mit.value

        self.fromat_nb_frame = Frame(self.init_window_name)
        self.fromat_nb_frame.grid(row=10, column=10)

        row_count = 1
        # 选择文件解析
        self.nb_title_label = Label(self.fromat_nb_frame, text='Select NB file to convert to MIT16:', fg='red')
        self.nb_title_label.grid(row=row_count, column=0, columnspan=3, sticky=W)

        row_count += 1
        # 起始时间输入
        self.start_time_nb_label = Label(self.fromat_nb_frame, text="Start Time", fg='black')
        self.start_time_nb_label.grid(row=row_count, column=0)
        st_default_value = StringVar()
        st_default_value.set('')
        self.start_time_nb_Text = Entry(self.fromat_nb_frame, textvariable=st_default_value)  # 开始时间
        self.start_time_nb_Text.grid(row=row_count, column=1)
        time_eg_label = Label(self.fromat_nb_frame, text="eg：2020-07-19 09:00:00", fg='black')
        time_eg_label.grid(row=row_count, column=2)

        row_count += 1
        self.nb_path_label = Label(self.fromat_nb_frame, text='File directory path:', fg='black')
        self.nb_path_label.grid(row=row_count, column=0)
        self.nb_path_Text = Entry(self.fromat_nb_frame, width=40)
        self.nb_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_nb_btn = Button(self.fromat_nb_frame, text="Choose file conversion", bg="lightblue",
                                       command=self.transform_nb_to_mit, fg='black')  # 调用内部方法  加()为直接调用
        self.select_nb_btn.grid(row=row_count, column=3)

        row_count += 1
        # 日志打印功能
        self.nb_log_label = Label(self.fromat_nb_frame, text='Log', fg='black')
        self.nb_log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.fromat_nb_frame, width=66, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=10)

    def transform_nb_to_mit(self):
        # 选择接收文件地址
        batch_path_array = tkinter.filedialog.askopenfilenames()
        self.nb_path_Text.delete(0, END)  # 删除之前输入框的内容
        self.nb_path_Text.insert(index=0, string=batch_path_array)  # 插入新选择的文件
        tooClass = ToolClass()
        # nb文件格式
        if batch_path_array[0].find('.nb') > 0:
            nb_file_name = batch_path_array[0]
            dir_name = tooClass.get_current_file_directory(nb_file_name)

            start_time_str = self.start_time_nb_Text.get()
            start_time_value = int(time.mktime(
                datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").timetuple())) * 1000

            read_file = ReadFile(ReadFile_log=self.write_log_to_Text)
            ecg_all = read_file.read_nb_file_content(nb_file_name)

            self.mkdir(dir_name + 'mit16')

            process_mit = ProcessMitData(mit_log=self.write_log_to_Text)
            process_mit.generate_mit_file('nalong' + '-' + str(start_time_value),128,[1000], ecg_all, start_time_value, None, dir_name + 'mit16/')


    # 下载体温APP的数据
    def download_TempData_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.download_tempServer.value

        self.download_temp_frame = Frame(self.init_window_name)
        self.download_temp_frame.grid(row=20, column=10)

        row_count = 1
        self.temp_title_label = Label(self.download_temp_frame, text='从体温服务器下载数据输入条件如下:', fg='red')
        self.temp_title_label.grid(column=0, columnspan=2, sticky=W)

        self.temp_app_label = Label(self.download_temp_frame, text='选择使用的APP:',fg='black')
        self.temp_app_label.grid(row=row_count, column=0)
        self.var_app_name1 = BooleanVar()
        self.var_app_name2 = BooleanVar()
        self.check_app_name1 = Checkbutton(self.download_temp_frame, text='感之度体温', variable=self.var_app_name1,fg='black')
        self.check_app_name1.grid(row=row_count, column=1)
        self.check_app_name2 = Checkbutton(self.download_temp_frame, text='Fever Scout', variable=self.var_app_name2,fg='black')
        self.check_app_name2.grid(row=row_count, column=2)

        row_count += 1
        # 设备号
        self.temp_sn_label = Label(self.download_temp_frame, text='设备号:',fg='black')
        self.temp_sn_label.grid(row=row_count, column=0)
        temp_sn_eg_label = Label(self.download_temp_frame, text='eg:F33.00112345',fg='black')
        temp_sn_eg_label.grid(row=row_count, column=2)
        temp_sn_default_value = StringVar()
        temp_sn_default_value.set('F33.00150424')
        self.temp_sn_Text = Entry(self.download_temp_frame, textvariable=temp_sn_default_value)
        self.temp_sn_Text.grid(row=row_count, column=1)

        row_count += 1
        # 起始时间输入
        temp_start_note_label = Label(self.download_temp_frame, text="起始时间",fg='black')
        temp_start_note_label.grid(row=row_count, column=0)
        st_default_value = StringVar()
        st_default_value.set('2021-01-05 09:00:00')
        self.temp_startTime_Text = Entry(self.download_temp_frame, textvariable=st_default_value)  # 开始时间
        self.temp_startTime_Text.grid(row=row_count, column=1)
        temp_startTime_eg_label = Label(self.download_temp_frame, text="eg：2020-07-19 09:00:00",fg='black')
        temp_startTime_eg_label.grid(row=row_count, column=2)

        row_count += 1
        # 结束时间输入
        temp_end_note_label = Label(self.download_temp_frame, text="结束时间",fg='black')
        temp_end_note_label.grid(row=row_count, column=0)
        et_default_value = StringVar()
        et_default_value.set('2021-01-05 15:06:36')
        self.temp_endTime_Text = Entry(self.download_temp_frame, textvariable=et_default_value)  # 结束时间
        self.temp_endTime_Text.grid(row=row_count, column=1)

        row_count += 1
        # 下载文件夹地址
        self.download_title = Label(self.download_temp_frame, text='下载数据存储地址:',fg='black')
        self.download_title.grid(row=row_count, column=0)
        self.download_path_Text = Entry(self.download_temp_frame, width=40)
        self.download_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        self.select_dl_btn = Button(self.download_temp_frame, text="选择下载地址", bg="lightblue",
                                    command=self.select_dl_filefolder,fg='black')  # 调用内部方法  加()为直接调用
        self.select_dl_btn.grid(row=row_count, column=3)

        row_count += 1
        # 开始下载解析
        self.start_download_ana_button = Button(self.download_temp_frame, text="开始下载并解析", fg="red",
                                                command=self.start_download_temp)  # 调用内部方法  加()为直接调用
        self.start_download_ana_button.grid(row=row_count, column=1, columnspan=2)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(self.download_temp_frame, text='日志',fg='black')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.download_temp_frame, width=66, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=10)
    def start_download_temp(self):
        appid1_value = self.var_app_name1.get()
        appid2_value = self.var_app_name2.get()
        app_id_str = ''
        if appid1_value and appid2_value:
            self.write_log_to_Text('不允许同时选择同时两个APP名')
            return
        if appid1_value == False and appid2_value == False:
            self.write_log_to_Text('请选择一个正在使用的APP名字')
            return
        if appid1_value:
            app_id_str = '感之度体温'
        if appid2_value:
            app_id_str = 'Fever Scout'
        self.write_log_to_Text(f'准备下载{app_id_str}APP的数据')

        sn_str = self.temp_sn_Text.get()
        start_time_str = self.temp_startTime_Text.get()
        end_time_str = self.temp_endTime_Text.get()

        if start_time_str.find('-') < 0 or start_time_str.find(':') < 0 or start_time_str.find(' ') < 0:
            self.write_log_to_Text('起始时间格式错误')
            return
        if end_time_str.find('-') < 0 or end_time_str.find(':') < 0 or end_time_str.find(' ') < 0:
            self.write_log_to_Text('结束时间格式错误')
            return
        start_time_value = time.mktime(
            datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").timetuple()) * 1000
        end_time_value = time.mktime(
            datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S").timetuple()) * 1000
        if end_time_value < start_time_value:
            self.write_log_to_Text('结束时间小于开始时间')

        if len(sn_str) != 12:
            self.write_log_to_Text('输入的体温设备号长度错误')
            return

        # isalpha()检查所有字符都是字母
        if sn_str[0].isalpha() and sn_str.find('.') > 0:
            download_temp = DownloadTemp(self.download_path_Text.get(),Download_Temp_Log=self.write_log_to_Text)
            if app_id_str == '感之度体温':
                temp_data = download_temp.download_temp_domestic(sn=sn_str,start_time=int(start_time_value),end_time=int(end_time_value),location=True,type=2)
                for temp_dict in temp_data:
                    temp_dict['displayTemp'] = temp_dict['processed']
                    temp_dict['battery'] = temp_dict['deviceBattery']
                draw_temp_view = DrawingView(write_path='',Draw_log=self.write_log_to_Text)
                draw_temp_view.draw_temp(temp_data)
            elif app_id_str == 'Fever Scout':
                temp_data = download_temp.download_temp_foreign(sn=sn_str,start_time=int(start_time_value),end_time=int(end_time_value),location=True,type=2)
                for temp_dict in temp_data:
                    temp_dict['displayTemp'] = temp_dict['processed']
                    temp_dict['battery'] = temp_dict['deviceBattery']

                draw_temp_view = DrawingView(write_path='', Draw_log=self.write_log_to_Text)
                draw_temp_view.draw_temp(temp_data)
        else:
            self.write_log_to_Text('设备名格式错误')

    # 分离多设备日志
    def splicy_multi_device_log_UI(self):
        self.destroy_frame(self.get_frame_value)
        self.get_frame_value = DestroyFrame.splicy_device_log.value

        self.splicy_log_frame = Frame(self.init_window_name)
        self.splicy_log_frame.grid(row=10, column=10)

        row_count = 0
        # 选择文件解析
        splicy_title_label = Label(self.splicy_log_frame, text='Select the files in the iOS mobile phone log where the data of multiple devices are logged together:', fg='red')
        splicy_title_label.grid(row=row_count, column=0, columnspan=4, sticky=W)

        row_count += 1
        splicy_path_label = Label(self.splicy_log_frame, text='File directory path:',fg='black')
        splicy_path_label.grid(row=row_count, column=0)
        self.splicy_path_Text = Entry(self.splicy_log_frame, width=40)
        self.splicy_path_Text.grid(row=row_count, column=1, columnspan=2, sticky=W)
        splicy_file_btn = Button(self.splicy_log_frame, text="Select the file to be separated", bg="lightblue",
                                      command=self.splicy_multi_device_log_action,fg='black')  # 调用内部方法  加()为直接调用
        splicy_file_btn.grid(row=row_count, column=3)

        row_count += 1
        # 开始下载解析
        self.splicy_start_analysis_btn = Button(self.splicy_log_frame, text="Start analysis", fg="red",
                                         command=self.start_splicy_file_analysis)  # 调用内部方法  加()为直接调用
        self.splicy_start_analysis_btn.grid(row=row_count, column=1, columnspan=2)

        row_count += 1
        # 日志打印功能
        self.log_label = Label(self.splicy_log_frame, text='Log',fg='black')
        self.log_label.grid(row=row_count, column=0)

        row_count += 1
        self.log_data_Text = Text(self.splicy_log_frame, width=90, height=30)  # 日志框
        self.log_data_Text.grid(row=row_count, column=0, columnspan=13)

    def splicy_multi_device_log_action(self):
        self.splicy_filefoler_path = tkinter.filedialog.askdirectory()
        self.write_log_to_Text('选择的文件夹:'+self.splicy_filefoler_path)
        # self.download_path_Text.select_clear()
        self.splicy_path_Text.delete(0, END)
        self.splicy_path_Text.insert(index=0, string=self.splicy_filefoler_path)


    def start_splicy_file_analysis(self):
        splicy_device_log = MultiDeviceSplicyLog(Splicy_log=self.write_log_to_Text)
        all_device_data = splicy_device_log.sord_file_data(self.splicy_filefoler_path)
        splicy_device_log.data_splicy_print(all_device_data,self.splicy_filefoler_path)
        splicy_device_log.splicy_file_log_analysis(self.splicy_filefoler_path)


    # 销毁上一个界面的UI
    def destroy_frame(self,destroy_value):
        '''
        :param destroy_value:需要销毁的视图的值
        :return:
        '''
        if destroy_value == DestroyFrame.download.value:
            self.download_frame.destroy()
        elif destroy_value == DestroyFrame.analysis.value:
            self.analysis_frame.destroy()
        elif destroy_value == DestroyFrame.mit.value:
            self.fromat_json_frame.destroy()
        elif destroy_value == DestroyFrame.ishne.value:
            self.fromat_ishne_frame.destroy()
        elif destroy_value == DestroyFrame.download_tempServer.value:
            self.download_temp_frame.destroy()
        elif destroy_value == DestroyFrame.splicy_device_log.value:
            self.splicy_log_frame.destroy()
        elif destroy_value == DestroyFrame.default.value:
            self.default_frame.destroy()
        elif destroy_value == DestroyFrame.nb_to_mit.value:
            self.fromat_nb_frame.destroy()
    # 创建文件夹
    def mkdir(self,dir_name):
        if not osp.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

    def analysis_mit16_file(self,file_path_name):
        process_mit = ProcessMitData(mit_log=self.write_log_to_Text)
        all_data = process_mit.read_mit16_data(file_path_name)

        drawing_view = DrawingView('',Draw_log=self.write_log_to_Text)
        drawing_view.draw_mit_ishne(all_data)

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
    root.title("VivaLNK DataTool")  # 窗口名
    width = 900
    height = 700
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    root.geometry(alignstr)

    # 创建一个顶级菜单
    menubar = Menu(root)

    my_app = MY_GUI(root)


    platform_type = platform.system()
    print(f"Current computer's system:{platform_type}")

    if platform_type == "Darwin":
        download_menu = Menu(menubar,tearoff=False)
        download_menu.add_command(label='vCloud Data Download',command=my_app.download_data_UI)
        menubar.add_cascade(label='Download',menu=download_menu)
    else:
        menubar.add_command(label='vCloud Data Download',command=my_app.download_data_UI)


    draw_menu = Menu(menubar, tearoff=False)
    menubar.add_cascade(label="Data Analysis and Graphing", menu=draw_menu)
    draw_menu.add_command(label="Data analysis and graphing", command=my_app.file_analysis_lost_UI)
    draw_menu.add_command(label="Data plot comparison", command=my_app.plot_comparison)

    # 文件转换
    convert_Menu = Menu(menubar, tearoff=False)
    menubar.add_cascade(label="ECG Format Conversion", menu=convert_Menu)
    convert_Menu.add_command(label="JSON to MIT16", command=my_app.format_json_mit_UI)
    convert_Menu.add_command(label="JSON to ISHNE", command=my_app.format_json_ishne_UI)
    convert_Menu.add_command(label='NB to MIT16',command=my_app.format_nb_mit_UI)

    # tempAPPMenu = Menu(menubar, tearoff=True)
    # menubar.add_cascade(label="体温APP", menu=tempAPPMenu)
    # tempAPPMenu.add_command(label="数据下载",command=my_app.download_TempData_UI)
    
    help_menu = Menu(menubar,tearoff=False)
    menubar.add_cascade(label='Help',menu=help_menu)

    other_menu = Menu(menubar,tearoff=False)
    menubar.add_cascade(label='Other',menu=other_menu)
    other_menu.add_command(label='Multi-device data log separation',command=my_app.splicy_multi_device_log_UI)


    if platform.system() == 'Darwin':
        othersMenu = Menu(menubar,tearoff=False)
        othersMenu.add_command(label='About', command=about_box)
        othersMenu.add_command(label='Exit', command=root.quit)
        menubar.add_cascade(label='Others',menu=othersMenu)
    else:
        menubar.add_command(label='About', command=about_box)
        menubar.add_command(label='Exit', command=root.quit)


    #  显示菜单
    root.config(menu=menubar)
    # root.bind_all("<Control-N>", lambda event: my_app.splicy_multi_device_log_UI())
    mainloop()

def about_box():
    showinfo(title='Change Log',message='Change Log:\nV2.4.10\n1. New parameter selection for drawing\n2. Add comparative analysis function')

if __name__ == "__main__":
    gui_start()




