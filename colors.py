from nanoleafapi import (
    RED,
    ORANGE,
    YELLOW,
    GREEN,
    LIGHT_BLUE,
    BLUE,
    PINK,
    PURPLE,
    WHITE,
)
from collections import namedtuple

BLACK = (0, 0, 0)

COLORS = [
    BLACK,
    RED,
    ORANGE,
    YELLOW,
    GREEN,
    LIGHT_BLUE,
    BLUE,
    PINK,
    PURPLE,
    WHITE,
]
palette = COLORS
whites = [
    (min(255, 2**i), min(255, 2**i), min(255, 2**i)) for i in range(10)
]

RGBA = namedtuple("RGBA", ["r", "g", "b", "a"])

TRANSLUCENT = RGBA(0, 0, 0, 0)
RGBA_COLORS = [TRANSLUCENT]

for color in COLORS:
    RGBA_COLORS.append(RGBA(*color, 255))


def make_background(dimensions, color):
    x, y = dimensions
    return [[color for _x in range(x)] for _y in range(y)]


BLUE_BACK = make_background((12, 6), RGBA(0, 0, 255, 255))
