import json
import datetime

class ToolClass:
    def __init__(self):
        pass

    def get_current_file_directory(self,file_name):
        '''获取当前文件的目录
        @param file_name 文件名
        :return 目录路径
        '''
        index = 0
        for i in range(0, len(file_name)):
            if file_name[i] == '/' or file_name[i] == '\\':
                index = i
        dir_name = file_name[0:index + 1]
        return dir_name

    def get_current_file_name(self,file_name_path):
        '''获取当前文件的名字
        @param file_name 文件名
        :return 目录路径
        '''
        index = 0
        for i in range(0, len(file_name_path)):
            if file_name_path[i] == '/' or file_name_path[i] == '\\':
                index = i
        file_name = file_name_path[index + 1:len(file_name_path)]
        return file_name


    def write_data_to_file(self,write_file_name, all_file_data):
        '''将json数据写入文件中
        @param write_file_name 文件名路径
        @param all_file_data 需要写入的json数组
        '''
        with open(write_file_name, "a+") as output:
            for line_dict in all_file_data:
                line_time_str = datetime.datetime.fromtimestamp(line_dict['recordTime'] / 1000).strftime(
                    '%Y-%m-%d %H:%M:%S')
                if 'denoiseEcg' in line_dict:
                    line_dict.pop('denoiseEcg')
                lines_str = line_time_str + ":" + json.dumps(line_dict) + '\n'
                # json.dump(line_dict, output)
                # output.write('\n')
                output.write(lines_str)
            output.close()

if __name__ == '__main__':
    tool = ToolClass()
    dir_name = tool.get_current_file_directory('/Users/cyanxu/Desktop/C5/VVDeviceDataLog 2021-02-1')
    dir_name1 = tool.get_current_file_name('/Users/cyanxu/Desktop/C5/VVDeviceDataLog 2021-02-1')
    print(dir_name)
    print(dir_name1)