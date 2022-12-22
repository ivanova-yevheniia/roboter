#!/usr/bin/env pybricks-micropython


# IMPORTS --------------------------------------------------------------------------------------------


# micropython imports
import time

# program imports
from global_vars import motorR, motorL, distance_handler, IO_HANDLER, color_sensor, LINE_THRESHOLD, TIME_T2_RIGHT, TIME_T2_LEFT, DISTANCE_WHILE_TURN
import main


# GLOBAL VARIABLES ---------------------------------------------------------------------------------

# lanes
lane = 1
lanes = 3


# STATES ------------------------------------------------------------------------------------------


class State:
    # override
    def act(self):
        raise Exception("State.act() not implemented")


class SensorStart(State):

    def __init__(self, next_state, buffer=3):
        self.release_time = None
        self.buffer = buffer
        self.next_state = next_state

    def act(self):
        if self.release_time is None:
            self.release_time = time.time() + self.buffer
        if time.time() <= self.release_time:
            return self
        else:
            return self.next_state


class SwitchOneRight(State):

    def __init__(self, n, d1, t1, t2, t3, d3=None, next_state=None):
        """
        Switches one line to the rights at speed n in the following pattern:
        - turning right for t1 seconds by reducing motor speed of right motor by d1
        - driving straight for t1 seconds with both motors at standard speed n
        - turning left for t3 seconds by reducing motor speed of left motor by d3, (default: d3 = d1)

        :param n: default motor speed in rotations per seconds
        :param d1: see description
        :param t1: see description
        :param t2: see description
        :param t3: see description
        :param next_state: state after the line switch
        :param d3: see description
        """
        global lane
        self.n = n

        self.d1 = d1
        if d3 is None:
            d3 = d1
        self.d3 = d3

        self.t0 = None
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        self.time_line_reached = None
        self.line_reached = False
        self.line_passed = False

        if next_state is None:
            next_state = LineFollowing.line_follower_right()
        self.next_state = next_state

    def act(self):
        global lane

        # saving the start time of line switch when called the first time
        if self.t0 is None:
            self.t0 = time.time()
            self.time_line_reached = self.t0 + self.t1 + self.t2
            distance_handler.set_mode(distance_handler.MODE_CHECK_DURING_RIGHT_TURN)

        # turning left during first phase
        if time.time() <= self.t0 + self.t1:
            motorR.run(self.n - self.d1)
            motorL.run(self.n)

        # going straight during second phase
        elif time.time() <= self.time_line_reached:
            motorR.run(self.n)
            motorL.run(self.n)
            if color_sensor.raw_value < LINE_THRESHOLD and self.line_reached is False:
                if distance_handler.distance() > DISTANCE_WHILE_TURN:
                    self.line_reached = True
                    self.time_line_reached = time.time()# + 0.005
                    # if self.line_passed:
                       #  distance_handler.turn_made(2)
                elif distance_handler.distance() < DISTANCE_WHILE_TURN and self.line_passed is False:
                    self.line_passed = True
                    # distance_handler.turn_made(1)


        # turning right during third phase
        elif time.time() <= self.time_line_reached + self.t3:
            # self.line_passed = False
            motorR.run(self.n)
            motorL.run(self.n - self.d3)

        # setting motors to default speed and returning the next state after third phase is done
        else:
            motorR.run(self.n)
            motorL.run(self.n)
            if not self.line_passed:
                lane += 1
                distance_handler.turn_made(lane)
            else:
                lane += 2
                distance_handler.turn_made(lane)
            return self.next_state

        # end of line switch was not reached, returning itself so this line switch is called again
        return self

    @staticmethod
    def create(next_state=None):
        next_state = LineFollowing.line_follower_right() if next_state is None else next_state
        return SwitchOneRight(n=400, d1=240, t1=1, t2=TIME_T2_RIGHT, d3=320, t3=0.6, next_state=next_state) # t2=1.3 before


class SwitchOneLeft(State):
    """
    Switches one line to the left at speed n in the following pattern:
    - turning left for t1 seconds by reducing motor speed of left motor by d1
    - driving straight for t1 seconds with both motors at standard speed n
    - turning right for t3 seconds by reducing motor speed of right motor by d3, (default: d3 = d1)

    :param n: default motor speed in rotations per seconds
    :param d1: see description
    :param t1: see description
    :param t2: see description
    :param t3: see description
    :param next_state: state after the line switch
    :param d3: see description
    """

    def __init__(self, n, d1, t1, t2, t3, d3=None, next_state=None):
        global lane

        self.n = n

        self.d1 = d1
        if d3 is None:
            d3 = d1
        self.d3 = d3

        self.t0 = None
        self.t1 = t1
        self.t2 = t2
        self.t3 = t3
        self.time_line_reached = None
        self.line_reached = False
        self.line_passed = False

        if next_state is None:
            next_state = LineFollowing.line_follower_left()
        self.next_state = next_state

    def act(self):
        global lane

        # saving the start time of line switch when called the first time
        if self.t0 is None:
            self.t0 = time.time()
            self.time_line_reached = self.t0 + self.t1 + self.t2
            distance_handler.set_mode(distance_handler.MODE_CHECK_DURING_LEFT_TURN)

        # turning right during first phase
        if time.time() <= self.t0 + self.t1:
            motorL.run(self.n - self.d1)
            motorR.run(self.n)

        # going straight during second phase
        elif time.time() <= self.time_line_reached:
            motorL.run(self.n)
            motorR.run(self.n)
            if color_sensor.raw_value < LINE_THRESHOLD and self.line_reached is False:
                if distance_handler.distance() > DISTANCE_WHILE_TURN:
                    self.line_reached = True
                    self.time_line_reached = time.time()# + 0.005
                    #if self.line_passed:
                    #     distance_handler.turn_made(0)
                elif distance_handler.distance() < DISTANCE_WHILE_TURN and self.line_passed is False:
                    self.line_passed = True
                    #distance_handler.turn_made(1)

        # turning left during third phase
        elif time.time() <= self.time_line_reached + self.t3:
            # self.line_passed = False
            motorL.run(self.n)
            motorR.run(self.n - self.d3)


        # setting motors to default speed and returning the next state after third phase is done
        else:
            motorL.run(self.n)
            motorR.run(self.n)
            if not self.line_passed:

                lane -= 1
                distance_handler.turn_made(lane)
            else:
                IO_HANDLER.print("We have passed away")
                lane -= 2
                distance_handler.turn_made(lane)
            return self.next_state

        # end of line switch was not reached, returning itself so this line switch is called again
        return self

    @staticmethod
    def create(next_state=None):
        next_state = LineFollowing.line_follower_left() if next_state is None else next_state
        return SwitchOneLeft(n=400, d1=240, t1=1, t2=TIME_T2_LEFT, d3=320, t3=0.6, next_state=next_state) # t2=1.3 before


class LineFollowing(State):

    LEFT = 0
    RIGHT = 1

    def __init__(self, n, Kp, Ki, Kd, side, log_every_nth=None):
        """
        PID line follower

        :param n: targeted speed, max value is n=1019
        :param Kp: Kp parameter for PID
        :param Ki: Ki parameter for PID
        :param Kd: Kd parameter for PID
        """

        self.state = 0

        self.side = side
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.n = n

        # 200er Regler
        self.Kp200 = 3.0
        self.Ki200 = 0.2
        self.Kd200 = 0.5
        self.n200 = 200

        # 400er Regler
        self.n400_error_thresh = 15
        self.n400_derivstive_threshold = 250
        self.last_error400 = None
        self.Kp400 = 4.5
        self.Ki400 = 0.25
        self.Kd400 = 1.0
        self.n400 = 400

        # 600er Regler
        self.n600_error_thresh = 7
        self.n600_derivstive_threshold = 125
        self.last_error600 = None
        self.Kp600 = 7.0
        self.Ki600 = 0.4
        self.Kd600 = 1.8
        self.n600 = 600

        # 800er Regler
        self.n800_error_thresh = 5
        self.n800_derivstive_threshold = 30
        self.last_error800 = None
        self.Kp800 = 9.5
        self.Ki800 = 0.55
        self.Kd800 = 4.0
        self.n800 = 800

        self.log_every_nth = log_every_nth
        self.log_i = 0

        self.t0 = None

    def act(self):

        if self.t0 is None:
            distance_handler.set_mode(distance_handler.MODE_CHECK_FORWARD)
            t = time.time()
            self.t0 = t
            self.last_error400 = t
            self.last_error600 = t
            self.last_error800 = t

        # color_sensor.read_sensor()

        # getting P, I, D values
        error = color_sensor.error
        integral = color_sensor.integral
        derivative = color_sensor.derivative

        # capping d value

        if derivative > 350:
            derivative = 350
        elif derivative < -350:
            derivative = -350

        # Choose controller, and set parameters
        t = time.time()
        if abs(error) > self.n400_error_thresh or abs(derivative) > self.n400_derivstive_threshold:
            self.last_error400 = t
            self.last_error600 = t
            self.last_error800 = t

        elif abs(error) > self.n600_error_thresh or abs(derivative) > self.n600_derivstive_threshold:
            self.last_error600 = t
            self.last_error800 = t

        elif abs(error) > self.n800_error_thresh or abs(derivative) > self.n800_derivstive_threshold:
            self.last_error800 = t

        if distance_handler.get_front_blocked():
            # IO_HANDLER.print("front blocked 200")
            self.n = self.n200
            self.Kp = self.Kp200
            self.Kd = self.Kd200
            self.Ki = self.Ki200

        elif t - self.last_error800 > 0.5:
            self.n = self.n800
            self.Kp = self.Kp800
            self.Kd = self.Kd800
            self.Ki = self.Ki800

        # elif t - self.last_error600 > 0.5:
        elif t - self.last_error600 > 0.8:
            # IO_HANDLER.print(str(error) + " " + str(derivative) + " 600")
            self.n = self.n600
            self.Kp = self.Kp600
            self.Kd = self.Kd600
            self.Ki = self.Ki600

        elif t - self.last_error400 > 0.3:
            # IO_HANDLER.print(str(error) + " " + str(derivative) + " 400")
            self.n = self.n400
            self.Kp = self.Kp400
            self.Kd = self.Kd400
            self.Ki = self.Ki400
        else:
            # IO_HANDLER.print(str(error) + " " + str(derivative) + " 200")
            self.n = self.n200
            self.Kp = self.Kp200
            self.Kd = self.Kd200
            self.Ki = self.Ki200

        # steuereingriff berechnen
        u = (self.Kp * error) + (self.Ki * integral) + (self.Kd * derivative)

        # logging (optional)
        if self.log_every_nth is not None:
            self.log_i += 1
            if self.log_i > self.log_every_nth:
                self.log_i = 0
                IO_HANDLER.log_params(param_names=["lf-time", "lf-e", "lf-i", "lf-d", "lf-u"],
                                       values=[time.time(), error, integral, derivative, u])
                # IO_HANDLER.log_param(param_name="lf-time", value=time.time())

        # setting motor speeds
        if self.side == LineFollowing.RIGHT:
            if u > 0:
                mLinks_n = self.n - u
                motorL.run(mLinks_n)
                motorR.run(self.n)
            else:
                mRechts_n = self.n + u
                motorL.run(self.n)
                motorR.run(mRechts_n)

        elif self.side == LineFollowing.LEFT:
            if u > 0:
                mRechts_n = self.n - u
                motorL.run(self.n)
                motorR.run(mRechts_n)
            else:
                mLinks_n = self.n + u
                motorL.run(mLinks_n)
                motorR.run(self.n)

        # deciding what the next state should be
        if time.time() - self.t0 > 0.5:
            self

        turn = main.distance_handler.get_turn()
        if turn == -1:
            return SwitchOneLeft.create()
        elif turn == 1:
            return SwitchOneRight.create()
        
        return self

    @staticmethod
    def line_follower_right(log_every_nth=None):
        # slow: n=200 kp=3 ki0.2 kd = 0.7
        # return LineFollowing(n=200, Kp=3.0, Ki=0.2, Kd=0.5, side=LineFollowing.RIGHT, log_every_nth=log_every_nth)
        return LineFollowing(n=600, Kp=3.0, Ki=0.2, Kd=0.5, side=LineFollowing.RIGHT, log_every_nth=log_every_nth)

    @staticmethod
    def line_follower_left(log_every_nth=None):
        # slow: n=200 kp=3 ki0.2 kd = 0.7
        # return LineFollowing(n=200, Kp=3.0, Ki=0.2, Kd=0.5, side=LineFollowing.LEFT, log_every_nth=log_every_nth)
        return LineFollowing(n=600, Kp=3.0, Ki=0.2, Kd=0.5, side=LineFollowing.LEFT, log_every_nth=log_every_nth)

# INITIALIZING GLOBAL STATES -------------------------------------------------------------


# global variables for important states that are used in the program


