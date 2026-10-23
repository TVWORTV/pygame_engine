from enum import Enum, auto


class ForceMode(Enum):
    FORCE = auto()
    IMPULSE = auto()
    ACCELERATION = auto()
    VELOCITY_CHANGE = auto()
