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


BPQM = 96
QUARTER = BPQM // 4
BAR4 = QUARTER * 4
PHRASE8 = BAR4 * 8
PHRASE4 = BAR4 * 4

EVERY_QUARTER = modmatch(QUARTER, 0)
EVERY_OFFBEAT = modmatch(QUARTER, QUARTER // 2)
EVERY_BAR4 = modmatch(BAR4, 0)
EVERY_PHRASE8 = modmatch(PHRASE8, 0)
EVERY_PHRASE4 = modmatch(PHRASE4, 0)


def mk_phrase8(fn=lambda c: print(" " * 8, c)):
    return (EVERY_PHRASE8, fn)


def mk_phrase4(fn=lambda c: print(" " * 8, c)):
    return (EVERY_PHRASE4, fn)


def mk_measure(fn=lambda c: print(" " * 2, c)):
    return (EVERY_BAR4, fn)


def mk_beat(fn=partial(print, "onbeat")):
    return (EVERY_QUARTER, fn)


def mk_offbeat(fn=partial(print, "offbeat")):
    return (EVERY_OFFBEAT, fn)


def on(trigger_fn, callback_fn):
    """Create a function
        `f(input)`
    that fires `callback_fn(input)` when `trigger_fn(input)` returns `True`
    """

    def _(input):
        if trigger_fn(input):
            callback_fn(input)

    return _


def nth(matcher_fn, callback_fn, container, n):
    """Like `on`, but keep a reference to instance and remove
    from listener container after `n` callbacks.
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
    """Like `on` but run only once before removing from listener container."""
    return nth(matcher_fn, callback_fn, container, 1)


class Beatomator:
    def __init__(self, listeners=[]):
        self.running = False
        self.counter = 0
        self.lasttick = 0
        self.listeners = listeners
        self.props = {}

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
        # TODO: Fix the semantics of delay:
        # are we executing callback the first time after delay?
        targetcount = self.counter + delay

        def croncallback(count):
            self.schedule(when, callback, repetitions)

        self.schedule(
            lambda count: targetcount == count,
            croncallback,
            1,
        )

    def schedule_next(self, grid, when, callback, repetitions=0):
        # TODO: Fix the semantics of delay:
        # are we executing callback the first time after delay?
        delay = ((self.counter // grid + 1) * grid) - self.counter
        return self.schedule_later(delay, when, callback, repetitions)

    def tick(self, min_bpm=10.0):
        t = monotonic()
        if not self.running or t - self.lasttick > (60.0 / min_bpm / 96.0):
            print(
                "setting 0",
                not self.running,
                t - self.lasttick,
                (60.0 / min_bpm / 96.0),
            )
            self.counter = 0
            self.running = True
        else:
            self.counter += 1
        self.lasttick = t
        for listener in self.listeners:
            listener(self.counter)


if __name__ == "__main__":

    def run(beatomator):
        while True:
            sleep(60.0 / 120.0 / 96.0)
            beatomator.tick()

    beatomator = Beatomator()
    for task in [mk_phrase(), mk_measure(), mk_beat(), mk_offbeat()]:
        beatomator.schedule(*task)

    beatomator.schedule_later(BAR4, EVERY_BAR4, partial(print, "NTH"), 5)

    run(beatomator)
