from shapes import ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, ZERO, blackout
from copy import deepcopy

import datetime

from draw import center, lshift, rshift, keyblend

NUMBERS = [ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE]

def now(military=None):
    shape = deepcopy(blackout)
    if military is None:
        military = datetime.datetime.now().strftime("%H%M")
    for i in range(len(military)):
        digit = int(military[i])
        num = NUMBERS[digit]
        shape = keyblend(rshift(num, i * 3), shape)
    return shape
