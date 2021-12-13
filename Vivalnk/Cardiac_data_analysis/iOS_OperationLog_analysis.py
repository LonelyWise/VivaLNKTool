#!/usr/bin/env python 
# coding:utf-8


with open('/Users/xuwei/Desktop/UCSF-AF ID425083 LOT SN 201936 C700102/Operation 2020-09-22 15-11.log','r') as file_to_read:
    while True:
        line = file_to_read.readline()
        if not line:
            break
        if line.find('connected') > 0:
            # line = line.replace(' ','')
            line = line.replace('\n','')
            print(line)
        if line.find('Did disconnect device') > 0:
            # line = line.replace(' ', '')
            line = line.replace('\n', '')
            print(line)
        # if line.find('flashNum') >= 0:
        #     line = line.replace(' ', '')
        #     line = line.replace('\n', '')
        #     print(line)