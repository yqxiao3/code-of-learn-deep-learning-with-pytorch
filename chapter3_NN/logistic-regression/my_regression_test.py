# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 09:11:16 2020
Try to learn deep learning from the simplest 2-dimension classification
@author: yongqin.xiao
"""

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from torch.autograd import Variable

# init the global variable input_data
data = []
data_size = 0


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


def sigmoid(x):
    return 1 / (1 + np.exp(-1 * x))


def logistic_regression(x):
    w = Variable(torch.randn(2, 1), requires_grad=True)
    b = Variable(torch.zeros(1), requires_grad=True)
    return F.sigmoid(torch.mm(x, w) + b)


def regression(input_data):
    # 1. convert list to numpy array
    np_data = np.array(input_data, dtype='float32')
    # 2 split to 2 arrays and attach two tensors to the 2 arrays
    points = torch.from_numpy(np_data[:, 0:2])
    expects = torch.from_numpy(np_data[:, -1]).unsqueeze(1)

    # print(points)
    # print("===")
    print(expects)


if __name__ == "__main__":
    data = read_data()
    regression(data)
    print(data_size)
    # paint(data1)
