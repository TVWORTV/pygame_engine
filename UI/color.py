from dataclasses import dataclass
from typing import Union
import re

@dataclass
class Color:
    value: Union[str, tuple[int, int, int, int]] = "#FFFFFFFF"
    hex: str = ""  

    def __post_init__(self):
        if isinstance(self.value, tuple):
            r, g, b, a = self.value
            for name, v in [("r", r), ("g", g), ("b", b), ("a", a)]:
                if not 0 <= v <= 255:
                    raise ValueError(f"{name}={v} must be 0-255")
            self.hex = f"#{r:02X}{g:02X}{b:02X}{a:02X}"
        else:
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?", self.value):
                raise ValueError(f"Invalid hex color: {self.value!r}")
            self.hex = self.value if len(self.value) == 9 else self.value + "FF"

    @property
    def rgba(self) -> tuple[int, int, int, int]:
        h = self.hex.lstrip("#")
        return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), int(h[6:8],16))