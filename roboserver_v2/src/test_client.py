#!/usr/bin/env pybricks-micropython

# IMPORTS ----------------------------------------------------------------------------
import random
import socket
import threading
import time


# LOGGING CODE ---------------------------------------------------------------------------

HOST, PORT = '127.0.0.1', 65433


class Logger:

    def __init__(self, value_names, log_every_nth=1):
        self.value_names = value_names
        self.every_nth = log_every_nth
        self.i = 0

    def log(self, values):
        """
        logs the state of the ColorSensorSensorhandler and the current time

        :param values: values to be logged
        """
        pass

    def log_specific_params(self, name_value_dict):
        """
        logs the state of the ColorSensorSensorhandler and the current time

        :param name_value_dict: dict of form {param_name: value, ...}for every parameter that is logged
        """
        values = []
        keys = name_value_dict.keys()
        for name in self.value_names:
            if name in keys:
                values.append(name_value_dict[name])
            else:
                values.append('E')
        self.log(values)

    def log_every_nth(self, values):
        self.i += 1
        if self.i > self.every_nth:
            self.i = 0
            self.log(values)

    def log_specific_params_every_nth(self, values):
        self.i += 1
        if self.i > self.every_nth:
            self.i = 0
            self.log_specific_params(values)


class Logger_ToFile(Logger):

    _count = 0

    def __init__(self, value_names, log_every_nth=1):
        super().__init__(value_names, log_every_nth)
        self.id_num = Logger_ToFile._count
        Logger_ToFile._count += 1
        self.files = [open('l' + str(self.id_num) + '_' + name + ".txt", 'w+') for name in self.value_names]

    def log(self, values):

        for i in range(len(values)):
            self.files[i].write(str(values[i]))
            self.files[i].write("\n")

    def __del__(self):
        for i in range(len(self.files)):
            self.files[i].close()


class Logger_NetworkConnection(Logger):

    _count = 0

    def __init__(self, value_names, host=HOST, port=PORT, log_every_nth=1):
        super().__init__(value_names, log_every_nth)
        # id
        self.id_num = Logger_NetworkConnection._count
        Logger_NetworkConnection._count += 1

        # networking
        self.host = host
        self.port = port + self.id_num
        self.value_names = value_names


        try:
            print("creating socket")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("socket created")
            s.bind((self.host, self.port))
            print("server " + str(self.id_num) + " listening")
            # ev3.speaker.beep()
            s.listen(10)
            self.conn, addr = s.accept()
            print("accepted")
            string = ",".join([name for name in value_names]) + "\n"
            data = string.encode('ascii')
            self.conn.send(data)
            self.conn.settimeout(25)
            s.close()

        except:
            print("connection failed")
            raise Exception("ColorSensorLogger_NetworkConnection: Connection to host failed")

    def log(self, values):
        string = ",".join([str(value) for value in values]) + '\n'
        data = string.encode('ascii')
        self.conn.send(data)

    def __del__(self):
        self.conn.close()


# LOG LOOP FOR LOGING DATA AT A GIVEN FREQUENCY---------------------------------------------------------------------


def logging_loop(functions, args, logger, frequency):
    """
    Logs the values returned from functions when called with args using the given logger at a given frequency
    Can be used as a target for a thread.

    :param functions: list of functions that are called to get the logged values
    :param args: arguments passed to the functions from function. Use None if one of the functions doesn't take any
    :param logger: instance of Logger that will be used to log the values created with functions
    :param frequency: the frequency the values will be logged
    """

    period = 1.0 / frequency

    t0 = time.time()
    t = t0 + period

    i = 0
    while True:
        values = []
        for i in range(len(functions)):
            values.append(functions[i](**args[i]))

        print(values)
        logger.log(values)

        # wait the rest of the period
        delta = t - time.time()
        if delta > 0:
            time.sleep(delta)
        t += period


# MAIN FOR TESTING -----------------------------------------------------------------------------

if __name__ == "__main__":

    logger1 = Logger_NetworkConnection(["time", "cs-v", "cs-e", "cs-i", "cs-d"], HOST, PORT, log_every_nth=2)
    # logger2 = Logger_NetworkConnection(["time", "cs-v", "cs-e", "cs-i", "cs-d"], HOST, PORT, log_every_nth=2)

    '''
    for i in range(1000):
        logger1.log([time.time(), 1, 2, 3, 4])
        # logger2.log([time.time(), 1, 2, 3, 4])
        time.sleep(0.5)
    '''

    value_functions = [time.time,
                       lambda: random.randint(0, 50),
                       lambda: random.randint(0, 50),
                       lambda: random.randint(0, 50),
                       # lambda: random.randint(0, 50),
                       # lambda: random.randint(0, 50),
                       lambda: random.randint(0, 50)]
    args = [{}, {}, {}, {}, {}]
    # args = [{}, {}, {}, {}, {}, {}, {}]
    thread = threading.Thread(target=logging_loop, args=(value_functions, args, logger1, 60))
    thread.start()

