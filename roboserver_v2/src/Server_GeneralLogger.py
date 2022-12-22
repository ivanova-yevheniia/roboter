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
HOST = '192.168.138.234'  # Standard loopback interface address (localhost)
FIRST_PORT = 65433  # Port to listen on (non-privileged ports are > 1023)

HOST, PORT = '127.0.0.1', 65433

deques_lock = threading.Lock()


class Plot:

    def __init__(self, plot_rows=2, plot_columns=2):
        self.plot_rows = plot_rows
        self.plot_columns = plot_columns
        self.fig = plt.figure()
        self.axes = []
        self.ani = None

        self.drawing_functions = []

    def add_drawing_function(self, func: function):
        self.drawing_functions.append(func)

    def draw_plot(self, i):
        for func in self.drawing_functions:
            func(i)

    def start(self):
        self.ani = animation.FuncAnimation(self.fig, self.draw_plot, interval=250)
        plt.show()


    def create_subplot(self):
        ax = self.fig.add_subplot(self.plot_rows, self.plot_columns,  len(self.axes)+1)
        self.axes.append(ax)
        return ax




class RobotServer:

    _count = 0

    def __init__(self, host, port, to_file=True, plot=None, plotted_time=10, plot_boundaries_dict=None):

        # connection params
        self.host: str = host
        self.port: int = port + RobotServer._count

        # plot params
        self.plot: Plot | None = plot
        self.plotted_time: int = plotted_time
        self.plot_boundaries_dict = plot_boundaries_dict if plot_boundaries_dict is not None else {}
        self.plot_boundaries_keys = self.plot_boundaries_dict.keys()

        # save to file params
        self.to_file: bool = to_file
        self.data_root = os.path.join(DATA_ROOT, 'l'+str(RobotServer._count))
        if os.path.exists(self.data_root):
            shutil.rmtree(self.data_root)
        os.makedirs(self.data_root, exist_ok=False)
        self.files = []

        # plotting
        if self.plot is not None:
            self.time_idx = -1
            self.deques = []
            self.axes = []
            self.graphs = []
            self.plot_names = []

        # updating server count
        RobotServer._count += 1

        # server init

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connecting")
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(20)
            self.sockFile = self.sock.makefile()
            print("connected")

            init_string = self.sockFile.readline().rstrip()
            init_params = init_string.split(",")

            j = 0
            for i, param_name in enumerate(init_params):
                if self.to_file:
                    self.files.append(open(os.path.join(self.data_root, f"{i}_{param_name}.txt"), 'w+'))
                if self.plot is not None:
                    if not param_name == "time":
                        ax = self.plot.create_subplot()
                        self.axes.append(ax)
                        self.plot_names.append(param_name)
                        j += 1
                    self.deques.append(collections.deque(np.array([])))
                if param_name == "time":
                    self.time_idx = i

            if self.plot is not None:
                self.plot.add_drawing_function(self.draw_plot)
                if self.time_idx == -1:
                    raise Exception("if plot is shown one parameter must be named 'time'")
        except:
            raise Exception("ColorSensorLogger_NetworkConnection: Establishing connection to host failed")

        # starting
        self.thread = threading.Thread(target=self.receive_data)
        self.thread.start()

    def receive_data(self):

        try:
            time_t0 = None
            while True:
                string = self.sockFile.readline().rstrip()
                params = string.split(",")

                # print(params, self.time_idx)

                if self.to_file:
                    # print(len(self.files))
                    # print(params)
                    for i in range(len(params)):
                        self.files[i].write(params[i])
                        self.files[i].write("\n")
                        self.files[i].flush()

                if self.plot is not None:

                    deques_lock.acquire()

                    _time = float(params[self.time_idx])
                    if time_t0 is None:
                        time_t0 = _time
                        _time = 0
                    else:
                        _time = _time - time_t0

                    for i in range(len(params)):
                        if i == self.time_idx:
                            self.deques[i].append(_time)
                        else:
                            self.deques[i].append(params[i])

                    while len(self.deques[self.time_idx]) > 0 and _time - self.deques[self.time_idx][0] > self.plotted_time:
                        for deque in self.deques:
                            deque.popleft()

                    deques_lock.release()

        except:
            raise Exception("ColorSensorLogger_NetworkConnection: Connection to host failed")

    def draw_plot(self, i):
        #print(i)
        #print(self.deques)

        # locking plotting data, as it shouldn't be changed while access
        deques_lock.acquire()

        k = 0
        for j in range(len(self.deques)):
            # print(f"j = {j},  k= {k}, time_idx = {self.time_idx}")
            if j == self.time_idx:
                continue
            print(f"{j}: {self.deques[j]}")
            self.axes[k].clear()
            # self.axes[k].set_title(self.plot_names[k])
            # self.axes[k].plot(self.deques[self.time_idx], self.deques[j])
            self.axes[k].set_ylim([-100, 100])
            self.axes[k].plot(self.deques[self.time_idx], self.deques[j])
            self.axes[k].set_ylim([-100, 100])
            # self.axes[k].set_ybounds(ymin=-100.0, ymax=100.0)

            # if self.plot_names[k] in self.plot_boundaries_keys:
            #    self.axes[k].set_ylim(self.plot_boundaries_dict[self.plot_names[k]])
            k += 1

        # plotting data no longer accessed
        deques_lock.release()


def draw_plot_with_stored_data(logger_num, boundaries=None, width=2):

    if boundaries is None:
        boundaries = {}
    boundaries_keys = boundaries.keys()

    data_root = os.path.join(DATA_ROOT, f"l{logger_num}")
    paths = sorted(os.listdir(data_root))

    heigth = math.ceil((len(paths)-1)/width)

    fig, axes = plt.subplots(heigth, width)
    names = []

    time_idx = None
    for i, path in enumerate(paths):
        if "_time.txt" in path:
            time_idx = i
        else:
            names.append(path.split('_')[-1].split('.')[0].strip())

    files = [open(os.path.join(data_root, path), 'r') for path in paths]
    arrays = []
    min_array_len = None
    for i, file in enumerate(files):
        if i == time_idx:
            org_times_array = [float(line.strip()) for line in file.readlines()]
            times_array = [org_times_array[i] - org_times_array[0] for i in range(len(org_times_array))]
            arrays.append(times_array)
        else:
            arrays.append([float(line.strip()) for line in file.readlines()])

        if min_array_len is None:
            min_array_len = len(arrays[i])
        else:
            min_array_len = len(arrays[i]) if len(arrays[i]) < min_array_len else min_array_len

    i = 0
    for j in range(len(arrays)):
        if j == time_idx:
            continue
        axes[i % width, math.floor(i / width)].clear()
        axes[i % width, math.floor(i / width)].set_title(names[i])
        if names[i] in boundaries_keys:
            axes[i % width, math.floor(i / width)].set_ylim(boundaries[names[i]])
        axes[i % width, math.floor(i / width)].plot(arrays[time_idx][:min_array_len], arrays[j][:min_array_len])
        i += 1
    plt.show()


if __name__ == "__main__":

    # prepare: erase old data

    print("1: socket connection + live plotting")
    print("2: plotting stored data")

    command = input().strip()

    if command == '1':
        plot = Plot(plot_rows=2, plot_columns=2)
        rs1 = RobotServer(host=HOST, port=FIRST_PORT, to_file=True, plot=plot)
        print("returned for es2")
        # rs2 = RobotServer(host=HOST, port=FIRST_PORT, to_file=True, plot=plot)
        time.sleep(2)
        # plot.start()
        # time.sleep(1000)
        plt.show()
        time.sleep(2)
        for i in range(2000):
            plot.draw_plot(i)
            time.sleep(0.5)
        time.sleep(1000)

    if command == '2':
        print()
        print("What Loggers do you use?")
        count = int(input())
        draw_plot_with_stored_data(count)
        time.sleep(1000)


