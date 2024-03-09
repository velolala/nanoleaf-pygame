from time import sleep, monotonic
from operator import mod as _mod
from functools import partial


def mod(matcher, target_value):
    # reverse the arguments for operator.mod and add target matching
    return (
        lambda input: partial(lambda b, a: _mod(a, b), matcher)(input)
        == target_value
    )


def on(trigger_fn, callback_fn):
    def _(input):
        if trigger_fn(input):
            callback_fn(input)

    return _


phrase = on(mod(96 * 4 * 8, 0), lambda c: print(" " * 8, c))
measure = on(mod(96 * 4, 0), lambda c: print(" " * 2, c))
beat = on(mod(96, 0), print)
offbeat = on(mod(96, 96 // 2), lambda c: print("offbeat"))


def tick(count):
    if True:
        print(count)


class BeatCounter:
    def __init__(self, listeners=[phrase, measure, beat, offbeat]):
        self.running = False
        self.counter = 0
        self.lasttick = None
        self.listeners = listeners

    def tick(self):
        t = monotonic()
        if not self.running or t - self.lasttick > (60.0 / 30.0 / 96.0):
            self.counter = 0
            self.running = True
        else:
            self.counter += 1
        self.lasttick = t
        for listener in self.listeners:
            listener(self.counter)


counter = BeatCounter()


def do_tick():
    counter.tick()


def run():
    while True:
        sleep(60.0 / 120.0 / 96.0)
        do_tick()


if __name__ == "__main__":
    run()
