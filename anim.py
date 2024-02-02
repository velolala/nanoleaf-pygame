from colors import COLORS
import time


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


if __name__ == "__main__":
    t = TimeTrigger(2)
    count = 0
    for signal in t:
        print(signal)
        time.sleep(0.1)
        count += 1
        if count > 20:
            break
