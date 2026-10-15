import re
from typing import Union


class Color:
    def __init__(self, *args: Union[str, tuple, int]):
        if len(args) == 0:
            args = ("#FFFFFFFF",)

        if len(args) == 1:
            value = args[0]
        elif len(args) in (3, 4):
            value = tuple(args)
        else:
            raise TypeError("Color takes a hex string, a tuple, or 3-4 integers")

        if isinstance(value, tuple):
            if len(value) == 3:
                value = value + (255,)
            if len(value) != 4:
                raise ValueError("Color tuple must have 3 or 4 components")
            for name, v in zip("rgba", value):
                if not 0 <= v <= 255:
                    raise ValueError(f"{name}={v} must be 0-255")
            r, g, b, a = value
            self.hex = f"#{r:02X}{g:02X}{b:02X}{a:02X}"
        else:
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?", value):
                raise ValueError(f"Invalid hex color: {value!r}")
            self.hex = value.upper() if len(value) == 9 else value.upper() + "FF"

    @property
    def rgba(self) -> tuple[int, int, int, int]:
        h = self.hex.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))

    def __eq__(self, other):
        return isinstance(other, Color) and self.hex == other.hex

    def __hash__(self):
        return hash(self.hex)

    def __repr__(self):
        return f"Color({self.hex!r})"