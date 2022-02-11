from app.engine import utils
from app.engine.base_class import ThreadBase
import gpiozero
from gpiozero.pins.pigpio import PiGPIOFactory

factory = PiGPIOFactory()

AXIS_WORLD = "yz"
DICT_DIRECTION_MAP = {"N": ("z", -1),  # North
                      "S": ("z", 1),  # South
                      "E": ("y", -1),  # East
                      "W": ("y", 1)  # West
                      }


class Servo:

    def __init__(self, gpio=-1, angle_steps=6):

        self._gpio = gpio
        self.motor = gpiozero.AngularServo(self._gpio, pin_factory=factory, min_angle=1.0, max_angle=179.0,
                                           initial_angle=90.0, min_pulse_width=0.0006, max_pulse_width=0.0024)
        self._current_angle = 90
        self.angle_step = round(180 / angle_steps, 1)
        self.move(angle=90)

    def __repr__(self):
        return f"Servo: [{self._gpio}] GPIO"

    @property
    def value(self):
        return self._current_angle

    def move(self, angle=90.0):
        try:
            self.motor.angle = angle

            if angle > self.motor.max_angle:
                self._current_angle = self.motor.max_angle
            elif angle < self.motor.min_angle:
                self._current_angle = self.motor.min_angle
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

        axis, direction = DICT_DIRECTION_MAP.get(side, ("", 0))

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

    def run(self) -> None:
        self.is_running = True


def main():
    def _calculate_inputs(input_str=""):
        input_str = input_str.strip()
        split_input = input_str.split(" ")
        sides = input_str
        angle = None
        if len(split_input) == 2:
            sides = split_input[0]
            angle = split_input[-1]
            if angle.isdigit():
                angle = int(angle)

        return sides, angle

    dict_pins = {
        # "pan_pin": 11, # BOARD
        "pan_pin": 17,  # BCM
        # "tilt_pin": 18 # BOARD
        "tilt_pin": 24  # BOARD
    }

    servo_controller = ServoController(**dict_pins)
    servo_controller.start()

    while True:

        try:
            input_str = input("Sides and angle: ")
            sides, angle = _calculate_inputs(input_str=input_str)
            servo_controller.move(sides=sides, angle=angle)

        except KeyboardInterrupt:
            del servo_controller
            break


# if __name__ == '__main__':
#     main()
