from time import sleep, monotonic
from operator import mod as _mod
from functools import partial


def modmatch(matcher, target_value):
    """Create a function
        `f(input)`
    that matches
        `input` % matcher == target_value."""
    # reverse the arguments for operator.mod and add target matching
    return (
        lambda input: partial(lambda b, a: _mod(a, b), matcher)(input)
        == target_value
    )


def on(trigger_fn, callback_fn):
    """Create a function
        `f(input)`
    that fires `callback_fn(input)` when `trigger_fn(input)` returns `True`
    """

    def _(input):
        if trigger_fn(input):
            callback_fn(input)

    return _


BPQM = 96
QUARTER = BPQM
BAR4 = BPQM * 4
PHRASE8 = BAR4 * 8

EVERY_QUARTER = modmatch(QUARTER, 0)
EVERY_OFFBEAT = modmatch(QUARTER, QUARTER // 2)
EVERY_BAR4 = modmatch(BAR4, 0)
EVERY_PHRASE8 = modmatch(PHRASE8, 0)

phrase = partial(on, EVERY_PHRASE8, lambda c: print(" " * 8, c))
measure = partial(on, EVERY_BAR4, lambda c: print(" " * 2, c))
beat = partial(on, EVERY_QUARTER, partial(print, "onbeat"))
offbeat = partial(on, EVERY_OFFBEAT, partial(print, "offbeat"))


def nth(matcher_fn, callback_fn, container, n):
    """Keep a reference to instance and remove from listener container
    after `n` callbacks.
    """
    instance = None
    executions = 0

    def callback(count):
        nonlocal instance
        nonlocal executions
        callback_fn(count)
        executions += 1
        if executions == n:
            container.remove(instance)

    instance = on(matcher_fn, callback)
    return instance


def once(matcher_fn, callback_fn, container):
    return nth(matcher_fn, callback_fn, container, 1)


class BeatCounter:
    def __init__(self, listeners=[phrase(), measure(), beat(), offbeat()]):
        self.running = False
        self.counter = 0
        self.lasttick = None
        self.listeners = listeners

    def schedule(self, when, callback, repetitions=0):
        """
        Args:
            `when(count) == True` then call
            `callback(count)` for
            `repetitions` times. `repetitions=0` means indefinitely.
        """
        if repetitions == 0:
            instance = on(when, callback)
        else:
            instance = nth(when, callback, self.listeners, repetitions)
        self.listeners.append(instance)

    def schedule_later(self, delay, when, callback, repetitions=0):
        targetcount = self.counter + delay

        def croncallback(count):
            self.schedule(when, callback, repetitions)

        self.schedule(
            lambda count: targetcount == count,
            croncallback,
            1,
        )

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

counter.schedule_later(BAR4, EVERY_BAR4, partial(print, "NTH"), 5)


def run():
    while True:
        sleep(60.0 / 120.0 / 96.0)
        counter.tick()


if __name__ == "__main__":
    run()
