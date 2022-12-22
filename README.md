# Roborace


Code für IST Roborace 2022 Winter


## robo_v1

The code running on the EV3 during runtime

### robo_v1.main

This file contains is run at to start executing the EV3 program
All other executable code (code after  if _ _name _ _ == "_ _ main _ _ ")
is used for testing specific models.

Implementation:
- creating ColorSensorPID + start parallel reading
- optional: creating and starting Logger

### robo_v1.states

This file defines states. States are situations the robot can be in. 
All States need to derive from State class and have to implement the state.act()
method. (not enforced, as abc not allowed on micropython).
The act() method defines how the robot has to behave. 
Implemetations
- LineFollowing:
  robot is currently  following the line. 
  act() does this using an PID controller
- SwitchRigth: moving 1 lane to the right
- ...


