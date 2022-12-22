#!/usr/bin/env pybricks-micropython

# IMPORTS ----------------------------------------------------------------------------

# micropython imports
import socket
# pybricks imports
import time

from pybricks.hubs import EV3Brick
# program import
from global_vars import HOST, PORT


# IO HANDLER CODE ---------------------------------------------------------------------------


class IOHandler:

    def print(self, message):
        raise Exception("Not implemented, use subclass")

    def log_param(self, param_name, value):
        raise Exception("Not implemented, use subclass")

    def log_params(self, param_names, values):
        raise Exception("Not implemented, use subclass")


# DUMMY HANDLER CODE ---------------------------------------------------------------------------


class DummyIOHandler(IOHandler):

    def print(self, message):
        pass

    def log_param(self, param_name, value):
        pass

    def log_params(self, param_names, values):
        pass


# NETWORK IO HANDLER ---------------------------------------------------------------------------

class NetworkIOHandler(IOHandler):

    def __init__(self, host=HOST, port=PORT):
        super().__init__()

        # networking
        self.host = host
        self.port = port

        ev3 = EV3Brick()
        try:
            # ev3.speaker.say("creating socket")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # ev3.speaker.say("socket created")
            s.bind((self.host, self.port))
            ev3.speaker.beep()
            s.listen(10)
            self.conn, addr = s.accept()
            # ev3.speaker.say("accepted")
            ev3.speaker.beep()
            self.conn.settimeout(None)
            s.close()

        except:
            ev3.speaker.say("connection failed")
            raise Exception("ColorSensorLogger_NetworkConnection: Connection to host failed")

    def print(self, message):
        string = "console$" + str(message) + "\n"
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

        """
        if os.path.exists(self.data_root):
            shutil.rmtree(self.data_root)
        os.makedirs(self.data_root, exist_ok=False)
        """

        self.files = {
            'console': open(self.data_root + 'console.txt', 'w+')
        }
        self.param_keys = ['console']

    def print(self, message):
        self.files['console'].write(str(message))
        self.files['console'].flush()

    def log_param(self, param_name, value):
        if param_name not in self.param_keys:
            path = self.data_root + param_name + '.txt'
            # if os.path.exists(path):
            #     raise Exception("FIle already exists: " + path)
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
