#!/usr/bin/env pybricks-micropython


# IMPORTS --------------------------------------------------------------------------------------------


# micropython imports
import time
import _thread

# pybricks imports
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import *
from pybricks.parameters import *

# program imports
from global_vars import *


# GLOBAL VARIABLES ---------------------------------------------------------------------------------


# lanes
lane = 1
lanes = 3


# DISTANCE SENSOR CODE -------------------------------------------------------------------------------

class DistanceSensorHandler:
    LEFT = 0
    RIGHT = 1

    MODE_CHECK_FORWARD = 0
    MODE_CHECK_DURING_RIGHT_TURN = 1
    MODE_CHECK_DURING_LEFT_TURN = 2
    MODE_CHECK_LEFT = 3
    MODE_CHECK_RIGHT = 4

    def __init__(self, port, wait_period, mode=MODE_CHECK_FORWARD):
        global lane, lanes
        self.sensor = UltrasonicSensor(port)
        self.current_angle = 0
        self.wait_period = wait_period
        self._targeted_lane = lane
        self._mode = mode
        self._front_blocked = False

        motorSmall.reset_angle(0)

    def set_mode(self, mode):
        self._mode = mode

        if mode == DistanceSensorHandler.MODE_CHECK_DURING_LEFT_TURN:
            motorSmall.run_target(200, -62, then=Stop.HOLD, wait=False)

        elif mode == DistanceSensorHandler.MODE_CHECK_DURING_RIGHT_TURN:
            motorSmall.run_target(200, 62, then=Stop.HOLD, wait=False)

        elif mode == DistanceSensorHandler.MODE_CHECK_FORWARD:
            motorSmall.run_target(200, 0, then=Stop.HOLD, wait=False)

    def checkNeighbouringLane(self, direction):
        if direction == DistanceSensorHandler.RIGHT:
            #motorSmall.run_target(500, -59, then=Stop.HOLD, wait=True) V1
            motorSmall.run_target(500, -60, then=Stop.HOLD, wait=True)
            distance = self.sensor.distance()
            # motorSmall.run_target(500, 50, then=Stop.HOLD, wait=False)
            time.sleep(0.5)
            if distance < 540: # 599
                return True
            else:
                return False
        elif direction == DistanceSensorHandler.LEFT:
            motorSmall.run_target(200, 55)
            if self.sensor.distance() < 540:
                return True
            else:
                return False
        else:
            raise Exception("1 oder 0 du Dulli!")

    def check_lanes(self):
        global lane, lanes
        while True:
            if self._mode == DistanceSensorHandler.MODE_CHECK_FORWARD:
                dist = self.sensor.distance()
                if dist < 450:
                    self._front_blocked = True
                if dist < 400:
                    # self._front_blocked = True
                    IO_HANDLER.print("chechk_lanes: lane, lanes, targeted = " + str(lane)+ ", " +  str(lanes) + ", " + str(self._targeted_lane))
                    if lanes == 3:
                        IO_HANDLER.print("I know we use 3 lanes, i am on" + str(lane) + "targeted " + str(self._targeted_lane))
                        if lane == 0:
                            self._targeted_lane = 1
                        elif lane == 1:
                            if self.checkNeighbouringLane(DistanceSensorHandler.RIGHT):
                                self._targeted_lane = 0
                            else:
                                self._targeted_lane = 2
                        elif lane == 2:
                            self._targeted_lane = 1

                    elif lanes == 2:
                        if lane == 0:
                            self._targeted_lane = 1
                        elif lane == 1:
                            self._targeted_lane = 0

                    IO_HANDLER.print("targeted after: "+ str(self._targeted_lane))
            else:
                self._front_blocked = False

            time.sleep(self.wait_period)

    def get_turn(self):
        global lane, lanes
        # IO_HANDLER.print("turn = " + str(self._targeted_lane) + " - " + str(lane))
        return self._targeted_lane - lane

    def get_front_blocked(self):
        return self._front_blocked

    def turn_made(self, current_lane):
        global lane
        lane = current_lane
        self._targeted_lane = current_lane
        IO_HANDLER.print("dist_sensor set to  lane, targeted_lane = " + str(lane) + str(self._targeted_lane))

    def distance(self):
        return self.sensor.distance()



