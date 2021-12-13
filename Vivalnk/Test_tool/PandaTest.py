

import pandas as pd
import pandas_profiling
import json

all_data = []
with open('/Users/weixu/Documents/维灵/数据分析/血氧数据/O2 1333_2021-08-31 11-50-00_12-10-00.txt','r') as file_to_read:
    while True:
        lines = file_to_read.readline()
        if not lines:
            break
        index = lines.index("{")
        lines = lines[index:len(lines)]
        json_dict = json.loads(lines)
        all_data.append(json_dict)




input_file_name = "/Users/weixu/Documents/维灵/数据分析/血氧数据/O2 1333.csv"
with open(input_file_name, "w") as output:
    output.write('pi,spo2\n')
    for dict in all_data:
        spo2 = dict['spo2']
        pi = dict['pi']

        write_value = str(pi) + ',' + str(spo2) + '\n'
        output.write(write_value)

    output.close()


data = pd.read_csv(input_file_name)

profile = data.profile_report(title='SpO2 Analysis')

profile.to_file(output_file='/Users/weixu/Documents/维灵/数据分析/血氧数据/'+'SpO2 Analysis.html')

# print(data)
# pandas_profiling.ProfileReport(data)




