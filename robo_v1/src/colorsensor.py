#!/usr/bin/env pybricks-micropython


# IMPORTS --------------------------------------------------------------------------------------------


# micropython imports
import _thread
import time
# pybricks imports
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import *
from pybricks.parameters import Port
# program imports
from global_vars import IO_HANDLER

# COLOR SENSOR CODE -------------------------------------------------------------------------------------


class ColorSensorHandler:

    def __init__(self,
                 port,
                 target_value,
                 frequency=50,
                 i_interval=1.0,
                 d_timediff=0.2,
                 d_average_count=3,
                 log_every_nth=None,
                 correction=None
                 ):
        """
        Create a Wrapper around the color sensor, providing P, I and D value

        :param port: Port of the color sensor on the EV3 brick
        :param target_value: The ambient light value targeted by the PID controller
        :param frequency: Frequency the sensor level is queried at
        :param i_interval: Time span in seconds over that the integral will be taken
        :param d_timediff: Time difference between the measurements used to calculate the average rate of change as Kd
        :param d_average_count: How many values at t1 and t2 are averaged to get the values used the average rate of change as Kd
        :param correction: CalibrationCorrection object used to correct the raw value read from the sensor, set to None if no calibration is done
        """

        # general
        self.sensor = ColorSensor(port)
        self.frequency = frequency
        self.correction = correction
        self.target = target_value

        # integral calculation params
        self.i_sum = 0.0
        self.i_values_count = int(i_interval * frequency)

        # derivative calculation params
        self.d_value = 0
        self.d_average_count = d_average_count
        self.d_first_old_value = int(d_timediff * frequency)
        self.d_timediff = self.d_first_old_value / frequency

        # value handling
        self.raw_value = 0.0
        self.value = 0.0
        self.values_length = max(self.i_values_count, self.d_first_old_value + self.d_first_old_value)
        self.values = [0.0 for _ in range(self.values_length)]
        self.values_pointer = -1

        # threading
        self.thread_lock = _thread.allocate_lock()

        # logging
        self.log_every_nth = log_every_nth
        self.log_i = 0

    def start(self):

        # initializing value storage with current value
        r, g, b = self.sensor.rgb()
        value = (r + g + b) / 3.0
        error = value - self.target
        self.values = [error for _ in range(self.values_length)]

        # start sensor thread
        _thread.start_new_thread(sensor_loop, (self, self.frequency))

    @property
    def error(self):
        return self.value

    @property
    def integral(self):
        integral = self.i_sum / self.frequency
        return integral

    @property
    def derivative(self):
        # lock thread while writing data
        self.thread_lock.acquire()

        current_value = 0.0
        old_value = 0.0
        for j in range(self.d_average_count):
            current_value += self.values[self.values_pointer - j]
            old_value += self.values[(self.values_pointer - self.d_first_old_value - j) % self.values_length]

        current_value /= self.d_average_count
        old_value /= self.d_average_count

        difference = current_value - old_value
        derivative = difference / self.d_timediff

        # reading is done
        self.thread_lock.release()

        return derivative

    def set_value(self, value):
        """
        takes new sensor values and stores it

        :param: the sensor value
        """
        # lock thread while writing data
        self.thread_lock.acquire()

        # save new value
        self.raw_value = value
        error = value - self.target
        self.value = error

        # update pointer
        self.values_pointer += 1
        if self.values_pointer >= self.values_length:
            self.values_pointer = 0

        # update integral
        self.i_sum -= self.values[self.values_pointer - self.i_values_count]
        self.i_sum += error

        # save value
        self.values[self.values_pointer] = error

        # writing done, releasing thread lock
        self.thread_lock.release()

    def read_sensor(self):
        """
        reads the sensor and stores the given value
        """
        r, g, b = self.sensor.rgb()
        value = (r + b + g) / 3.0
        if self.correction is not None:
            value = self.correction.correct(value)
        self.set_value(value)

        if self.log_every_nth is not None:
            self.log_i += 1
            if self.log_i > self.log_every_nth:
                self.log_i = 0
                IO_HANDLER.log_params(param_names=["cs-time", "cs-v", "cs-e", "cs-i", "cs-d"],
                                      values=[time.time(), self.raw_value, self.error, self.integral, self.derivative])


# SENSOR LOOP TO READ SENSOR AT A GIVEN FREQUENCY ---------------------------------------------------------


def sensor_loop(colorSensor, frequency):
    """
    Reads the ColorSensorHandler at a given frequency, and prints all values to file.
    Can be used as a target for a thread.

    :param colorSensor: the ColorSensorHandler on that .read_sensor() is called
    :param frequency: the frequency the sensor will be read at
    """

    period = 1.0 / frequency

    t0 = time.time()
    t = t0 + period

    i = 0
    while True:
        # read sensor
        colorSensor.read_sensor()

        # wait the rest of the period
        delta = t - time.time()
        if delta > 0:
            time.sleep(delta)
        t += period


# MAIN USED FOR TESTING THIS MODULE ----------------------------------------------------------------------


if __name__ == "__main__":
     pass