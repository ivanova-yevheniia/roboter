#!/usr/bin/env pybricks-micropython

# IMPORTS ----------------------------------------------------------------------------

# micropython imports
import math
import os
import random
import shutil
import socket
import time
# pybricks imports


HOST, PORT = '127.0.0.1', 65433
DATA_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'fileio_test_data1'))

# IO HANDLER CODE ---------------------------------------------------------------------------


class IOHandler:

    def print(self, message):
        raise Exception("Not implemented, use subclass")

    def log_param(self, param_name, value):
        raise Exception("Not implemented, use subclass")

    def log_params(self, param_names, values):
        raise Exception("Not implemented, use subclass")


# NETWORK IO HANDLER ---------------------------------------------------------------------------


class NetworkIOHandler(IOHandler):

    def __init__(self, host=HOST, port=PORT):
        super().__init__()

        # networking
        self.host = host
        self.port = port

        try:
            print("creating socket")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("socket created")
            s.bind((self.host, self.port))
            print("listening")
            s.listen(10)
            self.conn, addr = s.accept()
            print("accepted")
            self.conn.settimeout(None)
            s.close()

        except:
            print("connection failed")
            raise Exception("ColorSensorLogger_NetworkConnection: Connection to host failed")

    def print(self, message):
        string = "console$" + str(message) + '\n'
        data = string.encode('ascii')
        self.conn.send(data)

    def log_param(self, param_name, value):
        string = "$".join([param_name, str(value)]) + '\n'
        data = string.encode('ascii')
        self.conn.send(data)

    def log_params(self, param_names, values):
        string = "$".join([";".join([name for name in param_names]), ";".join([str(val) for val in values])]) + '\n'
        data = string.encode('ascii')
        self.conn.send(data)

    def __del__(self):
        self.conn.close()


# FILE IO HANDLER ---------------------------------------------------------------------------


class FileIOHandler(IOHandler):

    def __init__(self, data_root):
        super().__init__()

        self.data_root = data_root
        if os.path.exists(self.data_root):
            shutil.rmtree(self.data_root)
        os.makedirs(self.data_root, exist_ok=False)

        self.files = {
            'console': open(os.path.join(self.data_root, 'console.txt'), 'w+')
        }
        self.param_keys = ['console']

    def print(self, message):
        self.files['console'].write(str(message))
        self.files['console'].flush()

    def log_param(self, param_name, value):
        if param_name not in self.param_keys:
            path = os.path.join(self.data_root, param_name + '.txt')
            if os.path.exists(path):
                raise Exception("FIle already exists: " + path)
            self.param_keys.append(param_name)
            self.files[param_name] = open(path, 'w+')

        self.files[param_name].write(str(value))
        self.files[param_name].flush()

    def log_params(self, param_names, values):
        for i in range(len(param_names)):
            self.log_param(param_names[i], values[i])

    def __del__(self):
        for file in self.files.values():
            file.close()


if __name__ == "__main__":

    net_io = NetworkIOHandler()

    for i in range(10000):
        net_io.log_params(["time", "v", "e", "i", "d"], [time.time(),50*math.sin(i/25), 50*math.sin(i/25), 50*math.sin(i/25), 50*math.sin(i/25)])
        time.sleep(0.1)
    '''
    file_io = FileIOHandler(DATA_ROOT)

    file_io.print("HI")
    file_io.log_param('test1', 1)
    file_io.log_params(["test2", "test3", "test4"], [1.0, [12, 4.0], 5])
    '''
