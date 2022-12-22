#!/usr/bin/env pybricks-micropython


# IMPORTS --------------------------------------------------------------------------------------------


# micropython imports
import _thread
import states
import time
# pybricks imports
from pybricks.parameters import Port
# program imports
import colorsensor as cs
from global_vars import IO_HANDLER, color_sensor, distance_handler
import states

# STATE MACHINE ---------------------------------------------------------------------------------


def state_loop(state):
    while True:
        state = state.act()


# MAIN PROCEDURE OF EV3 PROGRAM ----------------------------------------------------------


# EV3 starts executing here
if __name__ == "__main__":




    # 1. starting sensors
    color_sensor.start()
    dist_thread = _thread.start_new_thread(distance_handler.check_lanes, ())
    
    # 3. run state machine in main thread
    state_loop(states.LineFollowing.line_follower_right(None))







