#!/usr/bin/env python 
# coding:utf-8
import os
import xlrd
import pandas as pd

filename = '/Users/weixu/Documents/维灵/Bionet版本的数据和报告/测试数据/12-1 运动数据/AILIN1725~1735/.~a870t-6daqe.xlsx'

def xlrd_read_excel():
    global filename
    xls_file = xlrd.open_workbook('/Users/weixu/Documents/维灵/Bionet版本的数据和报告/测试数据/12-1 运动数据/AILIN1725~1735/呼吸仪器.xls')

    # 打印所有sheet名称，是个列表
    sheet_name = xls_file.sheet_names()

    sh = xls_file.sheet_by_name(sheet_name[0])
    for i in range(sh.nrows):
        print(sh.row_values(i))



def panda_read_excel():

    df = pd.read_csv(filename)
    # 读取列名
    col_content = df.columns
    # 打印行名
    row_content = df.index
    # 打印10~20行前三列数据
    before_three_col = df.ix[10:20, 0:3]
    print(df.head(100))
    print(col_content)
    print(row_content)
    print(before_three_col)
    hr_filter = df[df.calories > 3.50]
    print(hr_filter)

if __name__ == '__main__':
    xlrd_read_excel()
    # panda_read_excel()
