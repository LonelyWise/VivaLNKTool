#!/usr/bin/env python
# coding:utf-8


import os
import json
import datetime

def read_spo2_file():
    with open('/Users/xuwei/Desktop/SpO2/O2 9801_1600927200000_1600930799999.log') as file_to_read:
        while True:
            lines = file_to_read.readline()
            if not lines:
                break
            spo2_array = json.loads(lines)

            with open('/Users/xuwei/Desktop/SpO2/SpO2.csv', "w") as output:
                output.write('时间,血氧,脉率,PI,电量\n')
                for spo2_dict in spo2_array:
                    record_time = spo2_dict['recordTime']
                    time_str = datetime.datetime.fromtimestamp(record_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    spo2_value = spo2_dict['spo2']
                    pi = spo2_dict['pi']
                    pr = spo2_dict['pr']
                    battery = spo2_dict['battery']
                    value = time_str +','+str(spo2_value)+','+str(pr)+','+str(pi)+','+str(battery)+'\n'
                    output.write(value)
                output.close()
if __name__ == "__main__":
    read_spo2_file()