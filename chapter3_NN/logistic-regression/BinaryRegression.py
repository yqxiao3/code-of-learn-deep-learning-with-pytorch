#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: XIAO Yongqin
@contact: yongqin.xiao@united-imaging.com
@file: BinaryRegression.py
@time: 2020/9/30 13:43
"""
import torch.nn as nn
import torch
from torch.autograd import Variable
import numpy as np
import matplotlib.pyplot as plt

data = []
data_size = 0
points = []
expects = []


class LogisticRegression(nn.Module):
    def __init__(self):
        super(LogisticRegression, self).__init__()
        self.lr = nn.Linear(2, 1)
        self.sm = nn.Sigmoid()

    def forward(self, x):
        x = self.lr(x)
        x = self.sm(x)
        return x


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

def build_plot(input_data):
    # distribute the points into 2 lists for '0' and '1'
    data_0 = list(filter(lambda i: 0 == i[-1], input_data))
    data_1 = list(filter(lambda i: 1 == i[-1], input_data))
    plot_x_0 = [i[0] for i in data_0]
    plot_y_0 = [i[1] for i in data_0]
    plot_x_1 = [i[0] for i in data_1]
    plot_y_1 = [i[1] for i in data_1]
    plt.plot(plot_x_0, plot_y_0, "ro")
    plt.plot(plot_x_1, plot_y_1, "go")
    #plt.show()


def ReArrangeData(input_data):
    global points, expects
    # 1. convert list to numpy array
    np_data = np.array(input_data, dtype='float32')
    # 2 split to 2 arrays and attach two tensors to the 2 arrays
    points = torch.from_numpy(np_data[:, 0:2])
    expects = torch.from_numpy(np_data[:, -1]).unsqueeze(1)


if __name__ == "__main__":
    print("Begin")
    logistic_model = LogisticRegression()
    criterion = nn.BCELoss()
    optimizer = torch.optim.SGD(logistic_model.parameters(), lr=1e-3, momentum=0.9)
    read_data()
    build_plot(data)
    ReArrangeData(data)
    # process the data
    for epoch in range(100000):
        x = Variable(points)
        y = Variable(expects)
        # =======  forward  ======
        out = logistic_model(x)
        loss = criterion(out, y)
        print_loss = loss.data
        mask = out.ge(0.5).float()
        correct = (mask == y).sum()
        acc = 1.0*correct / x.size(0)
        # =======  backward  ======
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if(epoch + 1) % 10000 == 0:
            print('*' * 10)
            print('epoch {}'.format(epoch+1))
            print('loss is {:.4f}'.format(print_loss))
            print('acc is {:.4f}'.format(acc))
    w0, w1 = logistic_model.lr.weight[0]
    w0 = w0.data
    w1 = w1.data
    b = logistic_model.lr.bias.data
    plot_x = torch.from_numpy(np.arange(0, 1, 0.001))
    plot_y = (-w0 * plot_x -b) / w1
    plt.plot(plot_x, plot_y)
    plt.show()


