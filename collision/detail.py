from enum import IntEnum


class DetailLevel(IntEnum):
    LOW = 8
    MEDIUM = 16
    HIGH = 32
    ULTRA = 64


class CapsuleDirection(IntEnum):
    VERTICAL = 0
    HORIZONTAL = 1
