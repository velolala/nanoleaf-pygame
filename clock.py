from shapes import (
    ONE,
    TWO,
    THREE,
    FOUR,
    FIVE,
    SIX,
    SEVEN,
    EIGHT,
    NINE,
    ZERO,
    blackout,
)
from copy import deepcopy

import datetime

from draw import center, hl_pixel, lshift, rshift, keyblend

NUMBERS = [ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE]


def now(military=None):
    shape = deepcopy(blackout)
    second = None
    if military is None:
        _now = datetime.datetime.now()
        military = _now.strftime("%H%M")
        second = _now.second
        ms = _now.microsecond

    for i in range(len(military)):
        digit = int(military[i])
        num = NUMBERS[digit]
        shape = keyblend(rshift(num, i * 3), shape)
    if second is not None and ms < 900000:
        shape = hl_pixel(shape, second % 12, int(second // 12))
        if second >= 50:
            shape = hl_pixel(shape, second % 12, int(second // 12) + 1)
        if second >= 54:
            for i in range(1, second - 54):
                shape = hl_pixel(shape, second % 12, int(second // 12) - i)

    return shape
