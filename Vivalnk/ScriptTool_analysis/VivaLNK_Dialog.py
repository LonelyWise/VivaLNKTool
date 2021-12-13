import tkinter
from enum import Enum

class SelectDrawFrame(Enum):
    default = 1
    comparison = 2

class MyDialog(tkinter.Toplevel):
    def __init__(self,type):
        super().__init__()
        self.title('绘制的波形参数选择')

        width = 600
        height = 200
        screenwidth = self.winfo_screenwidth()
        screenheight = self.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        self.geometry(alignstr)

        self.v = tkinter.StringVar()
        self.v.set('1')

        # 弹窗界面
        # self.setup_UI()
        if type == SelectDrawFrame.default.value:
            self.select_paramter_UI()
        elif type == SelectDrawFrame.comparison.value:
            self.select_paramter_comparison_UI()


    def select_paramter_UI(self):
        self.select_frame = tkinter.Frame(self)
        self.select_frame.grid(row=10, column=10)
        row_count = 0
        title_label = tkinter.Label(self.select_frame, text="Please check the parameters that need to be drawn, rwl needs to be drawn on the basis of ecg", fg='black')
        title_label.grid(row=row_count, column=0, columnspan=10)
        row_count += 1

        ecg_label = tkinter.Label(self.select_frame, text='ECG:', fg='black')
        ecg_label.grid(row=row_count, column=0)
        self.var_ecg_true = tkinter.BooleanVar()
        self.select_ecg_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_ecg_true, fg='black')
        self.select_ecg_btn.grid(row=row_count, column=1)

        rwl_label = tkinter.Label(self.select_frame, text='RWL:', fg='black')
        rwl_label.grid(row=row_count, column=2)
        self.var_rwl_true = tkinter.BooleanVar()
        self.select_rwl_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_rwl_true, fg='black')
        self.select_rwl_btn.grid(row=row_count, column=3)

        row_count += 1
        acc_label = tkinter.Label(self.select_frame, text='ACC:', fg='black')
        acc_label.grid(row=row_count, column=0)
        self.var_acc_true = tkinter.BooleanVar()
        self.select_acc_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_acc_true, fg='black')
        self.select_acc_btn.grid(row=row_count, column=1)

        row_count += 1
        hr_label = tkinter.Label(self.select_frame, text='HR:', fg='black')
        hr_label.grid(row=row_count, column=0)
        self.var_hr_true = tkinter.BooleanVar()
        self.select_hr_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_hr_true, fg='black')
        self.select_hr_btn.grid(row=row_count, column=1)

        row_count += 1
        rr_label = tkinter.Label(self.select_frame, text='RR:', fg='black')
        rr_label.grid(row=row_count, column=0)
        self.var_rr_true = tkinter.BooleanVar()
        self.select_rr_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_rr_true, fg='black')
        self.select_rr_btn.grid(row=row_count, column=1)

        row_count += 2
        self.cancel_btn = tkinter.Button(self.select_frame, text="Cancel", fg="red",
                                          command=self.cancel_select)  # 调用内部方法  加()为直接调用
        self.cancel_btn.grid(row=row_count, column=1)

        self.confirm_btn = tkinter.Button(self.select_frame, text="OK", fg="red",
                                          command=self.confirm_select)  # 调用内部方法  加()为直接调用
        self.confirm_btn.grid(row=row_count, column=2)

    def select_paramter_comparison_UI(self):
        self.select_frame = tkinter.Frame(self)
        self.select_frame.grid(row=10, column=10)
        row_count = 0
        title_label = tkinter.Label(self.select_frame,
                                    text="Please select the parameters to be compared for drawing",
                                    fg='black')
        title_label.grid(row=row_count, column=0, columnspan=10)
        row_count += 1

        ecg_label = tkinter.Label(self.select_frame, text='ECG:', fg='black')
        ecg_label.grid(row=row_count, column=0)
        self.var_ecg_true = tkinter.BooleanVar()
        self.select_ecg_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_ecg_true, fg='black')
        self.select_ecg_btn.grid(row=row_count, column=1)

        row_count += 1
        hr_label = tkinter.Label(self.select_frame, text='HR:', fg='black')
        hr_label.grid(row=row_count, column=0)
        self.var_hr_true = tkinter.BooleanVar()
        self.select_hr_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_hr_true, fg='black')
        self.select_hr_btn.grid(row=row_count, column=1)

        row_count += 1
        rr_label = tkinter.Label(self.select_frame, text='RR:', fg='black')
        rr_label.grid(row=row_count, column=0)
        self.var_rr_true = tkinter.BooleanVar()
        self.select_rr_btn = tkinter.Checkbutton(self.select_frame, variable=self.var_rr_true, fg='black')
        self.select_rr_btn.grid(row=row_count, column=1)

        row_count += 2
        self.cancel_btn = tkinter.Button(self.select_frame, text="Cancel", fg="red",
                                         command=self.cancel_select)  # 调用内部方法  加()为直接调用
        self.cancel_btn.grid(row=row_count, column=1)

        self.confirm_btn = tkinter.Button(self.select_frame, text="OK", fg="red",
                                          command=self.comparison_confirm_select)  # 调用内部方法  加()为直接调用
        self.confirm_btn.grid(row=row_count, column=2)


    def setup_UI(self):
        # 第一行（两列）
        row1 = tkinter.Frame(self)
        row1.pack(fill="x")
        tkinter.Label(row1, text='姓名：', fg='black',width=8).pack(side=tkinter.LEFT)
        self.name = tkinter.StringVar()
        tkinter.Entry(row1, textvariable=self.name, width=20).pack(side=tkinter.LEFT)
        # 第二行
        row2 = tkinter.Frame(self)
        row2.pack(fill="x", ipadx=1, ipady=1)
        tkinter.Label(row2, text='年龄：', fg='black',width=8).pack(side=tkinter.LEFT)
        self.age = tkinter.IntVar()
        tkinter.Entry(row2, textvariable=self.age, width=20).pack(side=tkinter.LEFT)
        # 第三行
        row3 = tkinter.Frame(self)
        row3.pack(fill="x")
        tkinter.Button(row3, text="取消", fg='black',command=self.cancel).pack(side=tkinter.RIGHT)
        tkinter.Button(row3, text="确定", fg='black',command=self.ok).pack(side=tkinter.RIGHT)

        self.row4 = tkinter.Frame(self)
        self.row4.pack(fill="x")
        tkinter.Checkbutton(self.row4, width=10,variable=self.v, fg='black',text='OFF',onvalue='ON', offvalue='OFF',command=self.click_event).pack(side=tkinter.RIGHT)


    def ok(self):
        self.userinfo = [self.name.get(), self.age.get()] # 设置数据
        self.destroy() # 销毁窗口
    def cancel(self):
        self.userinfo = None # 空！
        self.destroy()

    def click_event(self):
        print(self.v.get())
        self.row4["test"] = self.v.get()

    def confirm_select(self):
        print(f"{self.var_ecg_true.get()}   {self.var_acc_true.get()}   {self.var_hr_true.get()}    {self.var_rr_true.get()}")
        if self.var_ecg_true.get()==False and self.var_acc_true.get()==False and self.var_hr_true.get()==False and self.var_rr_true.get()==False:
            self.paramter = None
        else:
            self.paramter = {}
            self.paramter["ecg"] = self.var_ecg_true.get()
            self.paramter["acc"] = self.var_acc_true.get()
            self.paramter["hr"] = self.var_hr_true.get()
            self.paramter["rr"] = self.var_rr_true.get()
            self.paramter['rwl'] = self.var_rwl_true.get()
        self.select_frame.destroy()
        self.destroy()

    def comparison_confirm_select(self):
        print(f"{self.var_ecg_true.get()}  {self.var_hr_true.get()}    {self.var_rr_true.get()}")
        if self.var_ecg_true.get()==False and self.var_hr_true.get()==False and self.var_rr_true.get()==False:
            self.paramter = None
        else:
            self.paramter = {}
            self.paramter["ecg"] = self.var_ecg_true.get()
            self.paramter["hr"] = self.var_hr_true.get()
            self.paramter["rr"] = self.var_rr_true.get()
        self.select_frame.destroy()
        self.destroy()

    def cancel_select(self):
        self.paramter = None
        self.select_frame.destroy()
        self.destroy()