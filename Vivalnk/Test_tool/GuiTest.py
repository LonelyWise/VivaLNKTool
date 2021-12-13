import matplotlib.pyplot as plt

x_values = [1, 2, 3, 4, 25]
y_values = [1, 4, 9, 16, 25]
# s为点的大小
plt.scatter(x_values, y_values, s=100)

plt.plot([0,2000], [0,2000], color='b')

# 设置图表标题并给坐标轴加上标签
plt.title("Scatter pic", fontsize=24)
plt.xlabel("Value", fontsize=14)
plt.ylabel("Scatter of Value", fontsize=14)

# 设置刻度标记的大小
plt.tick_params(axis='both', which='major', labelsize=14)

plt.show()