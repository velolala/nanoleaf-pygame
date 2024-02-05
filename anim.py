from colors import COLORS
from osci import SineOscillator
import time
from random import randint


EMPTY = (0, 0, 0)


class TimeTrigger:
    def __init__(self, interval=2):
        self.time = time.monotonic
        self.interval = interval

    def __next__(self):
        now = self.time()
        # print(f"{now}, {self.interval}: {now % self.interval}")
        if now % self.interval < 1:
            return True
        else:
            return False

    def __iter__(self):
        return self


class RandomAnim:
    def __init__(self, FPS, dimensions=(12, 6)):
        self.width, self.height = dimensions
        self.osc = SineOscillator(FPS=FPS)
        self.dots = {}
        for i in range(randint(0, self.height)):
            self.dots[(randint(0, self.width), randint(0, self.height))] = (
                randint(0, 256),
                randint(0, 256),
                randint(0, 256),
            )

    def __iter__(self):
        return self

    def calculate_dots(self, signal):
        dots = {}
        for (x, y), (r, g, b) in self.dots.items():
            nx = x + signal
            nx %= self.width
            ny = y + signal
            ny %= self.height
            nr = r * signal % 255
            ng = min(255, g / (signal + 0.000001))
            nb = b * 5 * signal if signal > 0.5 else b
            dots[(nx, ny)] = (nr, ng, nb)
        self.dots = dots

    def __next__(self):
        signal = next(self.osc)
        print(signal)
        self.calculate_dots(signal)
        return self.to_shape(signal)

    def to_shape(self, signal):
        frame = []
        for y in range(self.height):
            line = []
            for x in range(self.width):
                line.append(
                    EMPTY if (x, y) not in self.dots else self.dots[(x, y)]
                )
            frame.append(line)
        return frame


if __name__ == "__main__":
    t = TimeTrigger(2)
    count = 0
    for signal in t:
        print(signal)
        time.sleep(0.1)
        count += 1
        if count > 20:
            break
