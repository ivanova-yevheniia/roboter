#!/usr/bin/env pybricks-micropython


# IMPORTS ------------------------------------------------------------------------------
import pybricks.ev3devices
from pybricks.ev3devices import Motor, UltrasonicSensor
from pybricks.parameters import Port
from pybricks.robotics import DriveBase

# GLOBAL VARIABLES ---------------------------------------------------------------------------------

# motors
motorL = Motor(Port.B)
motorR = Motor(Port.D)
drive_base = DriveBase(motorL, motorR, 55, 90)
motorSmall = Motor(Port.C)

us_sensor = pybricks.ev3devices.UltrasonicSensor(Port.S3)

# networking
HOST = "192.168.138.26"
PORT = 65433

# INPUT + OUTPUT
import dataio
# IO_HANDLER = dataio.NetworkIOHandler(host=HOST, port=PORT)
IO_HANDLER = dataio.DummyIOHandler()


# line switch
LINE_THRESHOLD = 29
TIME_T2_RIGHT = 1000  # 1.3
TIME_T2_LEFT = 1000  # 1.3
DISTANCE_WHILE_TURN = 400  # mm

# sensor wrappers
import colorsensor
color_sensor = colorsensor.ColorSensorHandler(Port.S1, target_value=25, frequency=200, i_interval=1.2, d_timediff=0.02,
                                              d_average_count=5, log_every_nth=None)  # Hell 86% Dunkel 6%
import distancesensor
distance_handler = distancesensor.DistanceSensorHandler(Port.S3, wait_period=0.05)