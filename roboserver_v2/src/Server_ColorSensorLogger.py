import collections
import socket
import os
import threading
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import numpy as np

DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'data1'))
HOST = '192.168.138.227'  # Standard loopback interface address (localhost)
PORT = 65433  # Port to listen on (non-privileged ports are > 1023)

HOST = '127.0.0.1'

class RoboServer:

    def __init__(self,
                 host: str,
                 port: int,
                 show_plot: bool = True,
                 plotted_time: int = 10,
                 save_to_file: bool = True,
                 save_file_directory: str = DATA_ROOT
                 ):

        """
        A TCP Client that receives data sent by the EV3 data and can log to file in /data directory
        and/or plot them to screen+console

        :param host: IP of the EV3 Brick
        :param port: port on the EV3 to connect to
        :param show_plot: Plot received data to screen [True/False]
        :param plotted_time: how many seconds should be visible in plot
        :param save_to_file: Write data to data directory? [True/False]
        :param save_file_directory: path of data directory. Defaults to /data
        """

        # connection params
        self.host: str = host
        self.port: int = port

        # plot params
        self.show_plot: bool = show_plot
        self.plotted_time: int = plotted_time

        # save to file params
        self.save_to_file: bool = save_to_file
        self.save_file_directory: str = save_file_directory

        # Create plot and temporary storage for values that are plotted
        if self.show_plot:

            # temporary storage for plotting data
            self.time_t0 = None
            self.time_deque = collections.deque(np.array([]))
            self.value1_deque = collections.deque(np.array([]))
            self.value2_deque = collections.deque(np.array([]))
            self.value3_deque = collections.deque(np.array([]))
            self.error_deque = collections.deque(np.array([]))
            self.integral_deque = collections.deque(np.array([]))
            self.derivative_deque = collections.deque(np.array([]))

            # plotting
            self.fig = plt.figure()
            # v1, v2 not needed as rgb is not used
            # self.ax_v1 = self.fig.add_subplot(3, 2, 1)
            # self.ax_v2 = self.fig.add_subplot(3, 2, 2)
            self.ax_v3 = self.fig.add_subplot(2, 2, 1)
            self.ax_e = self.fig.add_subplot(2, 2, 2)
            self.ax_i = self.fig.add_subplot(2, 2, 3)
            self.ax_d = self.fig.add_subplot(2, 2, 4)

        # File storage
        if self.save_to_file:
            self.file_time = open(os.path.join(self.save_file_directory, "1_time.txt"), 'w+')
            self.file_v1 = open(os.path.join(self.save_file_directory, "v1.txt"), 'w+')
            self.file_v2 = open(os.path.join(self.save_file_directory, "v2.txt"), 'w+')
            self.file_v3 = open(os.path.join(self.save_file_directory, "2_v3.txt"), 'w+')
            self.file_e = open(os.path.join(self.save_file_directory, "3_e.txt"), 'w+')
            self.file_d = open(os.path.join(self.save_file_directory, "5_d.txt"), 'w+')
            self.file_i = open(os.path.join(self.save_file_directory, "4_i.txt"), 'w+')

        # threading
        self.thread_lock = threading.Lock()
        self.socket_thread = threading.Thread(target=self._receive_data)

        # start functionality
        self.socket_thread.start()
        if self.show_plot:
            # self.ani = animation.FuncAnimation(self.fig, self._draw_plot, interval=200)
            time.sleep(5)
            plt.show()
            time.sleep(3)
            self._draw_plot(0)

    def _receive_data(self):

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("connecting")
            sock.connect((self.host, self.port))
            sock.settimeout(20)
            sockFile = sock.makefile()
            print("connected")

            while True:
                data = sockFile.readline()
                if not data:
                    break
                string = data# .decode('ascii')
                params = string.split(",")

                print(f"v={float(params[3]): .3f}   e={float(params[4]): .3f}   i={float(params[5]): .3f}    d={float(params[6]): .3f}")

                if self.save_to_file:
                    self.file_time.write(params[0])
                    self.file_v1.write(params[1])
                    self.file_v2.write(params[2])
                    self.file_v3.write(params[3])
                    self.file_e.write(params[4])
                    self.file_i.write(params[5])
                    self.file_d.write(params[6])
                    self.file_time.write("\n")
                    self.file_v1.write("\n")
                    self.file_v2.write("\n")
                    self.file_v3.write("\n")
                    self.file_e.write("\n")
                    self.file_i.write("\n")
                    # self.file_d.write("\n")
                    self.file_time.flush()
                    self.file_v1.flush()
                    self.file_v2.flush()
                    self.file_v3.flush()
                    self.file_e.flush()
                    self.file_i.flush()
                    self.file_d.flush()
                if self.show_plot:

                    self.thread_lock.acquire()

                    _time = float(params[0])
                    if self.time_t0 is None:
                        self.time_t0 = _time
                        _time = 0
                    else:
                        _time = _time - self.time_t0
                    self.time_deque.append(_time)
                    self.value1_deque.append(float(params[1]))
                    self.value2_deque.append(float(params[2]))
                    self.value3_deque.append(float(params[3]))
                    self.error_deque.append(float(params[4]))
                    self.integral_deque.append(float(params[5]))
                    self.derivative_deque.append(float(params[6]))

                    while len(self.time_deque) > 0 and _time - self.time_deque[0] > self.plotted_time:
                        self.time_deque.popleft()
                        self.value1_deque.popleft()
                        self.value2_deque.popleft()
                        self.value3_deque.popleft()
                        self.error_deque.popleft()
                        self.integral_deque.popleft()
                        self.derivative_deque.popleft()

                    self.thread_lock.release()

        except:
            raise Exception("ColorSensorLogger_NetworkConnection: Connection to host failed")

    def _draw_plot(self, i):

        # locking plotting data, as it shouldn't be changed while access
        self.thread_lock.acquire()

        # v1, v2 not needed as rgb is not used

        # self.ax_v1.clear()
        # self.ax_v1.plot(self.time_deque, self.value1_deque)

        # self.ax_v2.clear()
        # self.ax_v2.plot(self.time_deque, self.value2_deque)

        self.ax_v3.clear()
        self.ax_v3.plot(self.time_deque, self.value3_deque)
        self.ax_v3.set_ylim([0, 100])

        self.ax_e.clear()
        self.ax_e.plot(self.time_deque, self.error_deque)
        self.ax_e.set_ylim([-25, 25])

        self.ax_i.clear()
        self.ax_i.plot(self.time_deque, self.integral_deque)
        self.ax_i.set_ylim([-50, 50])

        self.ax_d.clear()
        self.ax_d.plot(self.time_deque, self.derivative_deque)
        self.ax_d.set_ylim([-50, 50])

        # plotting data no longer accessed
        self.thread_lock.release()


def draw_plot_with_stored_data():

    file_time = open(os.path.join(DATA_ROOT, "1_time.txt"), 'r')
    file_v1 = open(os.path.join(DATA_ROOT, "v1.txt"), 'r')
    file_v2 = open(os.path.join(DATA_ROOT, "v2.txt"), 'r')
    file_v3 = open(os.path.join(DATA_ROOT, "2_v3.txt"), 'r')
    file_e = open(os.path.join(DATA_ROOT, "3_e.txt"), 'r')
    file_i = open(os.path.join(DATA_ROOT, "4_i.txt"), 'r')
    file_d = open(os.path.join(DATA_ROOT, "5_d.txt"), 'r')

    times_array = [float(line.strip()) for line in file_time.readlines()]
    v1_array = [float(line.strip()) for line in file_v1.readlines()]
    v2_array = [float(line.strip()) for line in file_v2.readlines()]
    v3_array = [float(line.strip()) for line in file_v3.readlines()]
    e_array = [float(line.strip()) for line in file_e.readlines()]
    i_array = [float(line.strip()) for line in file_i.readlines()]
    d_array = [float(line.strip()) for line in file_d.readlines()]

    fig = plt.figure()
    # v1, v2 not needed as rgb is not used
    # ax_v1 = fig.add_subplot(3, 2, 1)
    # ax_v2 = fig.add_subplot(3, 2, 2)
    ax_v3 = fig.add_subplot(2, 2, 1)
    ax_e = fig.add_subplot(2, 2, 2)
    ax_i = fig.add_subplot(2, 2, 3)
    ax_d = fig.add_subplot(2, 2, 4)

    # v1, v2 not needed as rgb is not used

    # ax_v1.clear()
    # ax_v1.plot(time_array, value1_array)

    # ax_v2.clear()
    # ax_v2.plot(time_array, value2_array)

    ax_v3.clear()
    ax_v3.plot(times_array, v3_array)
    ax_v3.set_ylim([0, 100])

    ax_e.clear()
    ax_e.plot(times_array, e_array)
    ax_e.set_ylim([-50, 50])

    ax_i.clear()
    ax_i.plot(times_array, i_array)
    ax_i.set_ylim([-120, 120])

    ax_d.clear()
    ax_d.plot(times_array, d_array)
    ax_d.set_ylim([-100, 100])

    plt.show()




if __name__ == "__main__":

    print("1: socket connection + live plotting")
    print("2: plotting stored data")

    command = input().strip()

    if command == '1':
        server = RoboServer(HOST, PORT, save_to_file=True, show_plot=True)
        time.sleep(1000)

    if command == '2':
        draw_plot_with_stored_data()


