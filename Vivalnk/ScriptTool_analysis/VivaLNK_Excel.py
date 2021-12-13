
import xlrd
import time
import datetime
import os
import json

from ScriptTool_analysis.VivaLNK_Unity import ToolClass

class Read_Excel():
    def __init__(self):
        self.file_name = ''
        self.write_file_dir = ""

    def xlrd_read_excel(self):
        tool_class = ToolClass()
        dir_name = tool_class.get_current_file_directory(self.file_name)
        self.write_file_dir = os.path.join(dir_name, 'Respirator.txt')

        xls_file = xlrd.open_workbook(self.file_name)
        sheet_name = xls_file.sheet_names()

        sh = xls_file.sheet_by_name(sheet_name[0])

        data_array = []
        last_recordTime = 0
        for i in range(sh.nrows):
            print(sh.row_values(i))
            cell_array = sh.row_values(i)
            if cell_array[0].find('2021') == 0:
                record_time_str = str(cell_array[0])
                try:
                    record_time_value = time.mktime(datetime.datetime.strptime(record_time_str, "%Y-%m-%d %H:%M:%S").timetuple()) * 1000
                    last_recordTime = record_time_value
                except:
                    # record_time_value = time.mktime(datetime.datetime.strptime(record_time_str, "%Y%m/%d %H:%M:%S").timetuple()) * 1000
                    record_time_value = last_recordTime + 1000
                    last_recordTime = record_time_value
                rr_value = 0
                if cell_array[3] == "___" or cell_array[3] == "—-" or cell_array[3] == "" or cell_array[3] == "—":
                    rr_value = 0
                else:
                    rr_value = int(cell_array[3])

                dict = {}
                dict['recordTime'] = int(record_time_value)
                dict['rr'] = rr_value
                dict['leadOn'] = 1
                dict['flash'] = 0
                dict['ecg'] = [-221,-205,-194,-190,-191,-196,-186,-195,-204,-202,-202,-194,-205,-202,-196,-203,-205,-207,-194,-176,-183,-181,-179,-170,-157,-160,-165,-180,-177,-186,-176,-184,-177,-181,-181,-170,-160,-151,-180,-232,159,532,338,151,2,-103,-161,-183,-195,-203,-205,-194,-214,-223,-202,-200,-207,-213,-222,-230,-243,-248,-256,-274,-293,-296,-302,-294,-291,-276,-267,-246,-226,-218,-210,-182,-158,-133,-123,-109,-100,-82,-77,-67,-61,-57,-49,-35,-17,0,7,27,61,58,66,93,104,121,147,167,183,194,194,229,232,261,313,345,369,380,402,422,432,450,468,482,495,518,541,488,653,1147,1276,1100,950,811,731,709]
                dict['acc'] = [[1196,1633,-282],[1200,1626,-207],[1149,1675,-277],[1167,1691,-241],[1245,1609,-245],[1264,1656,-272],[1253,1716,-312],[1216,1667,-282],[1218,1619,-220],[1149,1753,-206]]
                data_array.append(dict)


        with open(self.write_file_dir, "a+") as output:
            for line_dict in data_array:
                line_time_str = datetime.datetime.fromtimestamp(line_dict['recordTime'] / 1000).strftime(
                    '%Y-%m-%d %H:%M:%S')
                lines_str = line_time_str + ":" + json.dumps(line_dict) + '\n'
                output.write(lines_str)
            output.close()


class ProcessExcel():
    def __init__(self):
        pass

    def process_temp_excel(self,all_file_data):
        """
        生成体温的csv文件
        """
        file_name = os.path.join('/Users/weixu/Desktop/未命名文件夹', "temp.csv")
        with open(file_name, "a+") as output:
            for i in range(len(all_file_data)):
                time_stamp = int(all_file_data[i]['recordTime']/1000)
                receive_time = int(all_file_data[i]['receiveTime']/1000)
                time_str = datetime.datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M:%S')
                receive_time_str = datetime.datetime.fromtimestamp(receive_time).strftime('%Y-%m-%d %H:%M:%S')

                rssi_str = 'N/A'
                if all_file_data[i]['flash'] == False:
                    rssi_str = str(all_file_data[i]['rssi'])
                write_line = f"{str(all_file_data[i]['deviceName'])},{str(all_file_data[i]['flash'])},{time_str},{str(all_file_data[i]['raw'])},{str(all_file_data[i]['display'])},{str(all_file_data[i]['fw'])},{receive_time_str},{rssi_str},{str(all_file_data[i]['battery'])}\n"
                if i == 0:
                    output.write('deviceName,flash,recordTime,raw,display,fw,receiveTime,rssi,battery\n')
                    output.write(write_line)
                else:
                    output.write(write_line)
            output.close()



if __name__ == "__main__":
    read_excel = Read_Excel()
    read_excel.file_name = "/Users/weixu/Documents/维灵/Bionet版本的数据和报告/测试数据/Round3/走路呼吸/yuki1032~1103-1208/yuki-Respirator-walk.xls"
    read_excel.xlrd_read_excel()