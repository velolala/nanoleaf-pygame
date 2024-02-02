import math
import time
from functools import partial


class Oscillator:
    def __init__(self, fun):
        self.fun = fun
        self.counter = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.counter += 1
        return self.fun(self.counter)


def sine(frame, freq=1, sr=5, _min=0.5, _max=0.7):
    if _max <= _min:
        raise ValueError(f"_min {_min} needs to be smaller than _max {_max}")
    # frame = frame % sr
    v = (math.pi * 2 * freq) / sr
    positive = (1 + math.sin(frame * v)) / 2
    return _min + (_max - _min) * positive


def SineOscillator(FPS=120, freq=1, _min=0, _max=1):
    return Oscillator(
        fun=partial(sine, sr=FPS, freq=freq, _min=_min, _max=_max)
    )


if __name__ == "__main__":
    FPS = 120
    osc = SineOscillator(FPS=FPS)
    for i in range(FPS * 10):
        print(next(osc))
        time.sleep(1 / FPS)
