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


def min_max(x, mi=0, mx=255):
    return min(255, max(0, x))


def mul_rgb(rgb, x):
    r, g, b = rgb
    return (
        min_max(r * x),
        min_max(g * x),
        min_max(b * x),
    )


def fadeout(shape, pct):
    shape = deepcopy(shape)
    for y, line in enumerate(shape):
        for x, pix in enumerate(line):
            shape[y][x] = mul_rgb(pix, pct)
    return shape


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
    if second is not None and ms > 850_000:
        shape = fadeout(shape, pct=1 - (ms - 850_000) / 990_000)
    if second is not None and ms < 850_000:
        shape = hl_pixel(shape, second % 12, int(second // 12))
        if second >= 50:
            shape = hl_pixel(shape, second % 12, int(second // 12) + 1)
        if second >= 54:
            for i in range(1, second - 54):
                shape = hl_pixel(shape, second % 12, int(second // 12) - i)

    return shape
