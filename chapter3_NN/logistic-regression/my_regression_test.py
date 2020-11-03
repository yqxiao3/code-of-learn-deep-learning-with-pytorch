# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 09:11:16 2020
Try to learn deep learning from the simplest 2-dimension classification
@author: yongqin.xiao
"""

import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import nn
import time
import os

# init the global variable input_data
data = []
data_size = 0
w = nn.Parameter(torch.randn(2, 1))
b = nn.Parameter(torch.zeros(1))
points = []
expects = []


def read_data():
    global data_size, data
    with open("./data.txt", "r") as f:
        # read input_data from input_data file
        data_list = [line.split("\n")[0].split(",") for line in f.readlines()]
        # convert to float
        data = [(float(d[0]), float(d[1]), float(d[2])) for d in data_list]
        # find the max value to map these values to 0~1
        x_max = max([x[0] for x in data])
        y_max = max([y[0] for y in data])
        # print(x_max,y_max)
        # update the value to input_data
        data = [(i[0] / x_max, i[1] / y_max, i[-1]) for i in data]
        data_size = len(data)
        f.close()
        return data


def paint(input_data):
    # distribute the points into 2 lists for '0' and '1'
    data_0 = list(filter(lambda i: 0 == i[-1], input_data))
    data_1 = list(filter(lambda i: 1 == i[-1], input_data))
    plot_x_0 = [i[0] for i in data_0]
    plot_y_0 = [i[1] for i in data_0]
    plot_x_1 = [i[0] for i in data_1]
    plot_y_1 = [i[1] for i in data_1]
    plt.plot(plot_x_0, plot_y_0, "ro")
    plt.plot(plot_x_1, plot_y_1, "go")
    plt.show()


def paint2(input_data):
    data_0 = list(filter(lambda i: 0 == i[-1], input_data))
    data_1 = list(filter(lambda i: 1 == i[-1], input_data))
    plot_x_0 = [i[0] for i in data_0]
    plot_y_0 = [i[1] for i in data_0]
    plot_x_1 = [i[0] for i in data_1]
    plot_y_1 = [i[1] for i in data_1]
    plt.plot(plot_x_0, plot_y_0, "ro")
    plt.plot(plot_x_1, plot_y_1, "go")
    plt.show()


def sigmoid(x):
    return 1 / (1 + np.exp(-1 * x))

def paint_sigmoid():
    plot_x = np.arange(-10,10.01,0.01)
    plot_y = sigmoid(plot_x)
    plt.plot(plot_x,plot_y,"r")
    plt.show()


def logistic_regression(x):
    global w,b
    return (torch.mm(x, w) + b).sigmoid()


def binary_loss(y_pred, y):
    logits = (y * y_pred.clamp(1e-12).log() + (1 - y) * (1 - y_pred).clamp(1e-12).log()).mean()
    return -logits


def ReArrangeData(input_data):
    global points, expects
    # 1. convert list to numpy array
    np_data = np.array(input_data, dtype='float32')
    # 2 split to 2 arrays and attach two tensors to the 2 arrays
    points = torch.from_numpy(np_data[:, 0:2])
    expects = torch.from_numpy(np_data[:, -1]).unsqueeze(1)


def Test1():
    data = read_data()
    ReArrangeData(data)
    optimizer = torch.optim.SGD([w, b], lr=1.0)
    start = time.time()
    for i in range(3):
        y_pred = logistic_regression(points)
        loss = binary_loss(y_pred, expects)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        # print(y_pred)
        # print(loss)
        # print(expects)
        # paint2(points)
        # mask = y_pred.ge(0.5).float()
        # acc = (mask == expects).sum().data[0] / expects.shape[0]
        # if (i + 1) % 20 == 0:
        #     print('epoch: {}, Loss: {:.5f}, Acc: {:.5f}'.format(i + 1, loss.data[0], acc))
    during = time.time() - start
    print()
    print('During Time: {:.3f} s'.format(during))

def Test2():
    file_path = "D:\\temp_data\\rib_05\\1.2.194.0.108707908.20200609222201.1397.12100.21155114\\1.2.156.112605.189250946103856.200609143609.3.6240.67186"
    print(os.path.split(file_path)[-1])
if __name__ == "__main__":
    Test2()
