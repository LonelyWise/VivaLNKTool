#!/usr/bin/env python
#模块pyplot包含很多生成图表的函数
import matplotlib.pyplot as plt
import numpy as np

input_values = [1,2,3,4,5,6]
squares = [1,4,9,16,25,36]
#plot()绘制折线图
plt.plot(input_values,squares,linewidth=5)
#np.array()将列表转换为存储单一数据类型的多维数组
x = np.array(input_values)
y = np.array(squares)
#annotate()给折线点设置坐标值
for a,b in zip(x,y):
    plt.annotate('(%s,%s)'%(a,b),xy=(1,b),xytext=(-20,10),
                 textcoords='offset points')
#设置标题
plt.title('Square Numbers',fontsize=24)
plt.xlabel('Value',fontsize=14)
plt.ylabel('Square of Value',fontsize=14)
#设置刻度的大小,both代表xy同时设置
plt.tick_params(axis='both',labelsize=14)
#show()打开matplotlib查看器，并显示绘制的图形
plt.show()



if __name__ == "__main__":
    from scipy import signal
    fs = 128
    low = 2
    high = 25
    order = 2
    b,a = signal.butter(order,Wn=[low/(fs/2),high/(fs/2)],btype="bandpass")
    zi = signal.lfilter_zi(b,a)
    print(b)
    print(a)
    print(zi)