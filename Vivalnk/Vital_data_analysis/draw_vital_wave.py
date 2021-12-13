#!/usr/bin/env python 
# coding:utf-8
import os
import matplotlib.pyplot as plt
import numpy as np

class DrawVitalWave:
    def __init__(self):
        pass

    def draw_acc(self,x_array,y_array,z_array):
        plt.figure(1)
        x = np.linspace(1, len(x_array), len(x_array), endpoint=True)
        ax = plt.subplot(3, 1, 1)
        plt.sca(ax)
        plt.plot(x, x_array, color='g')
        plt.ylim(-40, 40)
        plt.xlabel("Times")
        plt.ylabel("x")
        plt.title("X Wave")

        y = np.linspace(1, len(y_array), len(y_array), endpoint=True)
        ay = plt.subplot(3, 1, 2)
        plt.sca(ay)
        plt.plot(y, y_array, color='b')
        plt.ylim(-40, 40)
        plt.xlabel("Times")
        plt.ylabel("y")
        plt.title("Y Wave")

        z = np.linspace(1, len(z_array), len(z_array), endpoint=True)
        az = plt.subplot(3, 1, 3)
        plt.sca(az)
        plt.plot(y, y_array, color='r')
        plt.ylim(-40, 40)
        plt.xlabel("Times")
        plt.ylabel("z")
        plt.title("Z Wave")

        plt.show()

