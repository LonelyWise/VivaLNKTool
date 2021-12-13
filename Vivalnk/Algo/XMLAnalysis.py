import xml.dom.minidom



class RhythmObtain():
    def __init__(self):
        pass

    def obtainRhythm(self, start_time, xml_file_path):

        # '/Users/weixu/Documents/维灵/标记绘图/json_xml_3_pairs/1629004230350-1629078078089_denoised.xml'
        #打开xml文档
        dom = xml.dom.minidom.parse(xml_file_path)

        #得到文档元素对象
        root = dom.documentElement

        itemlist = root.getElementsByTagName('Section')

        rhythm_list = []
        for item in itemlist:
            # print(f'ID={item.getAttribute("id")}   name={item.getAttribute("name")}  itemsCount={item.getAttribute("itemsCount")}')

            if item.getAttribute("name") == "Rhythm annotations":
                rhythm_itemlist = item.getElementsByTagName("Rhythm")

                for rhythm_item in rhythm_itemlist:
                    stat_point = int(rhythm_item.getAttribute('start')) / 128
                    end_point = int(rhythm_item.getAttribute('end')) / 128

                    rhythm_tuple = [int(start_time/1000+stat_point),int(start_time/1000+end_point),rhythm_item.getAttribute('name')]
                    # print(stat_point, end_point)

                    # print(f"病症Id={rhythm_item.getAttribute('id')}   病症名={rhythm_item.getAttribute('name')}  开始点={rhythm_item.getAttribute('start')}   结束点={rhythm_item.getAttribute('end')}")

                    rhythm_list.append(rhythm_tuple)

        return rhythm_list