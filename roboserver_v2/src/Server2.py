import collections
import math
import shutil
import socket
import os
import threading
import time
import function

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import numpy as np

DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'data2'))
HOST = '192.168.138.26'  # Standard loopback interface address (localhost)
FIRST_PORT = 65433  # Port to listen on (non-privileged ports are > 1023)

# HOST, PORT = '127.0.0.1', 65433


class RobotServer:

    def __init__(self, host, port, data_root=DATA_ROOT, listeners=None, print_params=False):

        # connection params
        self.host: str = host
        self.port: int = port

        # save to file params
        self.data_root = data_root
        if os.path.exists(self.data_root):
            shutil.rmtree(self.data_root)
        os.makedirs(self.data_root, exist_ok=False)
        self.files = {
            'console': open(os.path.join(self.data_root, 'console.txt'), 'w+')
        }
        self.file_keys = []

        if listeners is None:
            listeners = {}
        self.listeners = listeners
        self.listeners['console'] = [lambda value: print(value)]


        # server init
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connecting")
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(20)
            self.sockFile = self.sock.makefile()
            print("connected")

        except:
            raise Exception("ColorSensorLogger_NetworkConnection: Establishing connection to host failed")

        # starting
        self.thread = threading.Thread(target=self.receive_data)
        self.thread.start()

    def add_listener(self, param_name, func):
        if param_name not in self.listeners.keys():
            self.listeners[param_name] = []
        self.listeners[param_name].append(func)

    def receive_data(self):

        #try:
        while True:
            string = self.sockFile.readline().rstrip()
            # print(string)
            if len(string) == 0:
                continue
            _names, _values = string.split("$")
            names = _names.split(";")
            values = _values.split(";")

            for i in range(len(names)):
                name = names[i]
                value = values[i]

                # add parameter if name not seen yet
                if name not in self.file_keys:
                    self.files[name] = open(os.path.join(self.data_root, name+'.txt'), 'w+')
                    self.file_keys.append(name)

                    if name not in self.listeners.keys():
                        self.listeners[name] = []

                # save to file
                self.files[name].write(value)
                self.files[name].write("\n")
                self.files[name].flush()

                # call listeners
                for listener in self.listeners[name]:
                    # print(f"listeners: {self.listeners[name]}")
                    # print(f"listener")
                    listener(value)

        #except:
        #    raise Exception("ColorSensorLogger_NetworkConnection: Connection to host failed")


class LiveSubPlot:

    def __init__(self, server, x_name, y_name, max_x_diff=None, ylim=None, xlim=None):
        self.x_name = x_name
        self.y_name = y_name
        self.server = server
        self.max_x_diff = max_x_diff
        self.ylim = ylim
        self.xlim = xlim

        self.x_deque = collections.deque(np.array([]))
        self.y_deque = collections.deque(np.array([]))

        self.server.add_listener(self.x_name, self.x_listener)
        self.server.add_listener(self.y_name, self.y_listener)

        self.next_x = None
        self.next_y = None

    def x_listener(self, value):
        self.next_x = (float(value))
        if self.next_y is not None:
            self.x_deque.append(self.next_x)
            self.y_deque.append(self.next_y)
            self.next_x = None
            self.next_y = None

        while not len(self.x_deque) == 0 and self.x_deque[-1] - self.x_deque[0] > self.max_x_diff:
            self.x_deque.popleft()
            self.y_deque.popleft()

        # print(f"{self.x_name}   x-listener: len(x) = {len(self.x_deque)},  len(y) = {len(self.y_deque)}")

    def y_listener(self, value):
        self.next_y = (float(value))
        if self.next_x is not None:
            self.x_deque.append(self.next_x)
            self.y_deque.append(self.next_y)
            self.next_x = None
            self.next_y = None

        while not len(self.x_deque) == 0 and self.x_deque[-1] - self.x_deque[0] > self.max_x_diff:
            self.x_deque.popleft()
            self.y_deque.popleft()

        # print(f"{self.x_name}   y-listener: len(x) = {len(self.x_deque)},  len(y) = {len(self.y_deque)}")

    @property
    def x_data(self):
        return self.x_deque

    @property
    def y_data(self):
        return self.y_deque


class LivePlot:

    def __init__(self, subplots, plot_rows, plot_columns):
        self.subplots = subplots
        self.fig = plt.figure()
        self.axes = []
        self.ani = None

        for i in range(len(self.subplots)):
            self.axes.append(self.fig.add_subplot(plot_rows, plot_columns,  i+1))

    def start(self):
        self.ani = animation.FuncAnimation(self.fig, self.draw_plot, interval=250)
        plt.show()

    def draw_plot(self, i):
        for j in range(len(self.axes)):
            self.axes[j].clear()
            self.axes[j].plot(self.subplots[j].x_data, self.subplots[j].y_data)
            if self.subplots[j].ylim is not None:
                self.axes[j].set_ylim(self.subplots[j].ylim)
            if self.subplots[j].xlim is not None:
                self.axes[j].set_xlim(self.subplots[j].xlim)


class FileSubPlot:

    def __init__(self, x_name, y_name, max_x_diff=None, data_root=DATA_ROOT, ylim=None, xlim=None):
        self.x_name = x_name
        self.y_name = y_name
        self.data_root = data_root
        self.max_x_diff = max_x_diff
        self.xlim = xlim
        self.ylim = ylim

        x_path = os.path.join(data_root, x_name+".txt")
        y_path = os.path.join(data_root, y_name + ".txt")

        x_file = open(x_path, 'r')
        y_file = open(y_path, 'r')

        self.x_array = []
        self.y_array = []

        for line in x_file.readlines():
            if len(line) == 0:
                continue
            self.x_array.append(float(line.strip()))

        for line in y_file.readlines():
            if len(line) == 0:
                continue
            if len(self.y_array) >= len(self.x_array):
                break
            self.y_array.append(float(line.strip()))
        length = min(len(self.x_array), len(self.y_array))
        self.x_array = self.x_array[:length]
        self.y_array = self.y_array[:length]

    @property
    def x_data(self):
        return self.x_array

    @property
    def y_data(self):
        return self.y_array


class FilePlot:

    def __init__(self, subplots, plot_rows, plot_columns):
        self.subplots = subplots
        self.fig = plt.figure()
        self.axes = []
        self.ani = None

        for i in range(len(self.subplots)):
            self.axes.append(self.fig.add_subplot(plot_rows, plot_columns,  i+1))

        for j in range(len(self.axes)):
            self.axes[j].clear()
            self.axes[j].plot(self.subplots[j].x_data, self.subplots[j].y_data)
            if self.subplots[j].ylim is not None:
                self.axes[j].set_ylim(self.subplots[j].ylim)
            if self.subplots[j].xlim is not None:
                self.axes[j].set_xlim(self.subplots[j].xlim)

        plt.show()


if __name__ == "__main__":

    # prepare: erase old data

    print("1: socket connection + live plotting")
    print("2: plotting stored data")

    command = input().strip()

    if command == '1':
        rs1 = RobotServer(host=HOST, port=FIRST_PORT, data_root=DATA_ROOT)

        time.sleep(1)

        sp1 = LiveSubPlot(server=rs1, x_name="lf-time", y_name="lf-e", max_x_diff=7, ylim=[-100, 100])
        sp2 = LiveSubPlot(server=rs1, x_name="lf-time", y_name="lf-i", max_x_diff=7, ylim=[-50, 50])
        sp3 = LiveSubPlot(server=rs1, x_name="lf-time", y_name="lf-d", max_x_diff=7, ylim=[-150, 150])
        sp4 = LiveSubPlot(server=rs1, x_name="lf-time", y_name="lf-u", max_x_diff=7, ylim=[-250, 250])
        plot = LivePlot([sp1, sp2, sp3, sp4], plot_rows=2, plot_columns=2)
        # plot.start()

        time.sleep(1000)

    if command == '2':
        sp1 = FileSubPlot(data_root=DATA_ROOT, x_name="lf-time", y_name="lf-e", max_x_diff=10, ylim=[-100, 100])
        sp2 = FileSubPlot(data_root=DATA_ROOT, x_name="lf-time", y_name="lf-i", max_x_diff=10, ylim=[-50, 50])
        sp3 = FileSubPlot(data_root=DATA_ROOT, x_name="lf-time", y_name="lf-d", max_x_diff=10, ylim=[-150, 150])
        sp4 = FileSubPlot(data_root=DATA_ROOT, x_name="lf-time", y_name="lf-u", max_x_diff=10, ylim=[-250, 250])
        plot = FilePlot([sp1, sp2, sp3, sp4], plot_rows=2, plot_columns=2)


