from app.engine import utils
from app.engine import angle_servo_ctrl
from app.engine.base_class import ThreadBase

AXIS_WORLD = "yz"
DICT_DIRECTION_MAP = {"N": ("z", -1),   # North
                      "S": ("z", 1),    # South
                      "E": ("y", -1),   # East
                      "W": ("y", 1)     # West
                      }

# optimizing the delay to reduce jitter
def cast_delay(ang, prev_ang):
    # minimum delay using max speed 0.1s/60 deg
    return (10.0 / 6.0) * (abs(ang - prev_ang)) / 1000.0


class Servo:

    def __init__(self, gpio=-1, angle_steps=6):

        self._gpio = gpio
        self._current_angle = 90
        self.angle_step = round(180/angle_steps, 1)
        self.move(angle=90)

    def __repr__(self):
        return f"Servo: [{self._gpio}] GPIO"

    @property
    def value(self):
        return self._current_angle

    def move(self, angle=90.0):
        try:
            delay = cast_delay(angle, self._current_angle)
            angle_servo_ctrl.move(self._gpio, angle, delay)
            if angle > 180:
                self._current_angle = 180
            elif angle < 0:
                self._current_angle = 0
            else:
                self._current_angle = angle
            return True
        except ValueError:
            return False

    def move_by_step(self, direction=0):
        new_angle = self._current_angle - self.angle_step if direction < 0 else self._current_angle + self.angle_step
        return self.move(new_angle)


class ServoController(ThreadBase):

    def __init__(self, axis_order=AXIS_WORLD,
                 orient=(1, 1),
                 pan_pin=11,
                 tilt_pin=18, *args, **kwargs):

        super(self.__class__, self).__init__()

        self.name = str(self.__class__.__name__)
        self.log_manager = utils.LogManager(self.name)

        self.axis_order = axis_order
        self.orient = orient
        self._is_moving = False
        self.dict_servos = {"y": Servo(gpio=pan_pin, angle_steps=6),
                            "z": Servo(gpio=tilt_pin, angle_steps=6)}

        for axis_ in self.dict_servos:
            self.log_manager.log(f"{axis_}: {self.dict_servos[axis_]}")

    def is_moving(self):
        return self._is_moving

    def get_axis_direction(self, side=""):

        axis, direction = DICT_DIRECTION_MAP.get(side, ("",0))

        if self.axis_order != AXIS_WORLD:
            if axis in AXIS_WORLD:
                index = AXIS_WORLD.index(axis)
                axis = self.axis_order[index]

                if index < len(self.orient):
                    direction *= self.orient[index]

        return axis, direction

    def move_by_sides(self, sides=""):

        self._is_moving = True
        for side_ in sides:
            axis, direction = self.get_axis_direction(side=side_.upper())
            if axis in self.dict_servos:
                self.dict_servos[axis].move_by_step(direction=direction)
            self.log_manager.log(f"axis: {axis}, direction: {direction}")
        self._is_moving = False

    def move_by_axis(self, axis="", angle=None):

        self._is_moving = True
        if axis in self.dict_servos:
            if angle is not None:
                self.dict_servos[axis].move(angle=angle)
                self.log_manager.log(f"axis: {axis}, angle: {angle}")
        self._is_moving = False

    def move(self, sides="", angle=None):

        if list(set(sides) & set(DICT_DIRECTION_MAP.keys())):
            self.move_by_sides(sides=sides)
        elif list(set(sides) & set(AXIS_WORLD)) and angle is not None:
            self.move_by_axis(axis=sides, angle=angle)

    def get_data(self):

        dict_result = {}
        for axis_ in self.dict_servos:
            servo_ = self.dict_servos.get(axis_)
            if servo_:
                dict_result[axis_] = servo_.value

        return dict_result

    # def loop_inputs(self):
    #
    #     try:
    #         while True:
    #             key_input = input("Key input: ").lower()
    #             for char_ in key_input:
    #                 self.move_by_sides(key_name=char_)
    #     except KeyboardInterrupt:
    #         del self
    #         pass


#
# def main():
#     # servo_ctl = ServoController(axis_order="zy", orient=(-1, 1))
#     servo_ctl = ServoController()
#     servo_ctl.loop_inputs()
#     pass
#
# if __name__ == '__main__':
#     main()
#
