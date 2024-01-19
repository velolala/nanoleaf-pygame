from itertools import chain, repeat

EMPTY = (0, 0, 0)


def rshift(shape, i, wrap=False):
    if i == 0:
        return shape
    if wrap:
        return [line[-i:] + line[:-i] for line in shape]
    else:
        return [i * [EMPTY] + line[:-i] for line in shape]


def lshift(shape, i, wrap=False):
    if wrap:
        return [line[i:] + line[:-i] for line in shape]
    else:
        return [line[i:] + [EMPTY] * i for line in shape]


def bounce(shape, speed, wrap=False):
    yield from repeat(lshift(shape, 1, wrap), speed)
    yield from repeat(shape, speed)
    yield from repeat(rshift(shape, 1, wrap), speed)
    yield from repeat(shape, speed)
    yield from repeat(lshift(shape, 1, wrap), speed // 3)
    yield from repeat(lshift(shape, 2, wrap), speed // 3)
    yield from repeat(lshift(shape, 1, wrap), speed // 3)
    yield from repeat(shape, speed)
    yield from repeat(rshift(shape, 1, wrap), speed // 3)
    yield from repeat(rshift(shape, 2, wrap), speed // 3)
    yield from repeat(rshift(shape, 1, wrap), speed // 3)
    yield from repeat(shape, speed)


def ushift(shape, i, wrap=False):
    if wrap:
        return shape[i:] + shape[:i]
    return shape[i:] + [[EMPTY] * len(shape[0]) for _ in range(i)]


def dshift(shape, i, wrap=False):
    if wrap:
        return shape[-i:] + shape[: len(shape) - i]
    return [[EMPTY] * len(shape[0]) for _ in range(i)] + shape[:-i]


def dissolve(shape):
    yield shape
    for i in range(len(shape[0])):
        yield lshift(shape, i)[: len(shape) // 2] + rshift(shape, i)[
            len(shape) // 2 :
        ]


def all_zero(shape):
    count = 0
    while all(all(p == EMPTY for p in line[:count]) for line in shape):
        count += 1
    return count


def center(shape):
    pre = all_zero(shape)
    suf = all_zero([line[::-1] for line in shape])
    if suf == pre:
        return shape
    margin = (suf + pre) // 2
    if margin == 0:
        return shape
    if pre < suf:
        return rshift(shape, margin - pre)
    if suf < pre:
        return lshift(shape, margin - suf)
    return shape


def scroll_in(shape):
    for left in range(all_zero([line[::-1] for line in shape]), 0, -1):
        yield lshift(shape, left)
    for right in range(0, len(shape[0])):
        yield rshift(shape, right)


def scroll(shape, wrap=True):
    width = len(shape[0])
    for i in range(width):
        yield rshift(shape, i, wrap=wrap)


def fade(frames, target):
    for i in range(1, frames + 1):
        yield min(1, 1.0 / i + target)


def to_rgb(shape, palette, fade=1):
    return [
        [palette[int(pix)] for pix in line]
        for line in shape.strip().split("\n")
    ]


def to_pixerator(shape):
    for y, line in enumerate(shape):
        for x, pix in enumerate(line):
            yield x, y, pix


def draw(s, shape, palette=None, fade=1):
    for x, y, pix in to_pixerator(shape):
        s.set_at((x, y), pix)
