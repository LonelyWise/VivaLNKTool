
import ECGAnalysis

'''
用于绘图分析的，将数据导出为csv格式
'''

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-f", "--filePath", type=str, help="json的文件路径,必填")
    # parser.add_argument("-o", "--output", type=str, help="输出的文件路径,必填")
    #
    # args = parser.parse_args()
    #
    # if args.filePath is None:
    #     parser.print_help()
    #     sys.exit(1)
    # else:
    #     if not os.path.exists(args.filePath):
    #         print('filePath not exists')
    #         sys.exit(1)
    #
    # if args.output is None:
    #     parser.print_help()
    #     sys.exit(1)

    json_file_name = "/Users/weixu/Documents/维灵/标记绘图/json_xml_3_pairs/1629085490089-1629091666089_denoised.json"

    handle = ECGAnalysis.DataHandle()
    print(handle.__doc__)
    handle.read_json_file(json_file_name)



