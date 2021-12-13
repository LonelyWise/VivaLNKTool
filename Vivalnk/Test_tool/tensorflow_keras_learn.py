import matplotlib.pyplot as plt
import numpy as np
import keras

from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense,Dropout,Flatten,Activation,Conv2D,MaxPooling2D

#载入数据，如果没有会自动从网上下载
(X_train,Y_train),(X_test,Y_test) = mnist.load_data()
print(X_train.shape)
print(Y_train.shape)
print(X_test.shape)
print(Y_test.shape)

plt.imshow(X_train[2115,:,:])
plt.show()
print(Y_train[2115])

#把输入整理成模型可以接受的格式
X_train=X_train.reshape(60000,28,28,1)
X_test=X_test.reshape(10000,28,28,1)

#查看输入的范围
print(np.max(X_train))
print(np.min(X_train))

#对输入进行归一化处理
X_train= X_train/255
X_test = X_test/255
print(np.max(X_test))
print(np.min(X_test))

from keras import utils as np_utils
#对于输出进行one-hot-coding
Y_train=np_utils.to_categorical(Y_train,10)
Y_test=np_utils.to_categorical(Y_test,10)
print(Y_train.shape)
print(Y_test.shape)

plt.imshow(X_test[100,:,:,0])
print(Y_test[100,:])
plt.show()

#搭建模型
model = Sequential()
model.add(Conv2D(32,(3,3),input_shape=(28,28,1)))# 卷积层
model.add(Activation("relu"))    #激活层
model.add(Conv2D(32,(3,3)))      # 卷积层
model.add(Activation("relu"))    #激活层
model.add(MaxPooling2D(pool_size=(2,2))) #池化层

model.add(Conv2D(64,(3,3)))
model.add(Activation("relu"))
model.add(Conv2D(64,(3,3)))
model.add(Activation("relu"))
model.add(MaxPooling2D(pool_size=(2,2)))

model.add(Flatten())
model.add(Dense(200))  #全连接层 200个神经元
model.add(Activation("relu"))
model.add(Dense(200)) #全连接层 200个神经元
model.add(Activation("relu"))
model.add(Dense(10,activation="softmax"))

#查看模型和参数统计
model.summary()

#定义模型的优化器
adam = keras.optimizers.Adam(lr=0.001,beta_1=0.9,beta_2=0.999,epsilon=1e-8)
model.compile(loss="categorical_crossentropy",optimizer=adam,metrics=["accuracy"])

#训练模型
model.fit(X_train,Y_train,batch_size=100,epochs=1,verbose=1,validation_data=[X_test,Y_test])