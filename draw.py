from itertools import repeat
from copy import deepcopy
from pygame import Color

EMPTY = (0, 0, 0)


def color_to_shape(shape, color):
    shape = deepcopy(shape)
    return [[color for _ in line] for line in shape]


def hl_pixel(shape, x, y):
    shape = deepcopy(shape)
    r, g, b = shape[y][x]
    if sum((r, g, b)) < 500:
        shape[y][x] = (
            min(255, int(r * 1.5) + 60),
            min(255, int(g * 1.5) + 60),
            min(255, int(b * 1.5) + 60),
        )
    else:
        shape[y][x] = (
            max(0, int(r * 0.5) + 20),
            max(0, int(g * 0.5) + 20),
            max(0, int(b * 0.5) + 20),
        )
    return shape


def keyblend(shape, backdrop, key=EMPTY):
    shape = deepcopy(shape)
    kr, kg, kb = key[:3]
    for y, line in enumerate(shape):
        for x, pix in enumerate(line):
            sr, sg, sb = pix[:3]
            if sr == kr and sg == kg and sb == kb:
                shape[y][x] = backdrop[y][x]
    return shape


def rshift(shape, i, wrap=False):
    shape = deepcopy(shape)
    if i == 0:
        return shape
    if wrap:
        return [line[-i:] + line[:-i] for line in shape]
    else:
        return [i * [EMPTY] + line[:-i] for line in shape]


def lshift(shape, i, wrap=False):
    shape = deepcopy(shape)
    if wrap:
        return [line[i:] + line[:i] for line in shape]
    else:
        return [line[i:] + [EMPTY] * i for line in shape]


def swap(shape, h=False, v=False):
    shape = deepcopy(shape)
    if h is True:
        shape = [list(reversed(line)) for line in shape]
    if v is True:
        shape = list(reversed(shape))
    return shape


def bounce(shape, speed, wrap=False):
    shape = deepcopy(shape)
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
    shape = deepcopy(shape)
    if wrap:
        return shape[i:] + shape[:i]
    return shape[i:] + [[EMPTY] * len(shape[0]) for _ in range(i)]


def dshift(shape, i, wrap=False):
    shape = deepcopy(shape)
    if wrap:
        return shape[-i:] + shape[: len(shape) - i]
    return [[EMPTY] * len(shape[0]) for _ in range(i)] + shape[:-i]


def dissolve(shape):
    shape = deepcopy(shape)
    yield shape
    for i in range(len(shape[0])):
        yield (
            lshift(shape, i)[: len(shape) // 2]
            + rshift(shape, i)[len(shape) // 2 :]
        )


def all_zero(shape):
    shape = deepcopy(shape)
    count = 0
    while all(all(p == EMPTY for p in line[:count]) for line in shape):
        count += 1
    return count


def center(shape):
    shape = deepcopy(shape)
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
    shape = deepcopy(shape)
    for left in range(all_zero([line[::-1] for line in shape]), 0, -1):
        yield lshift(shape, left)
    for right in range(0, len(shape[0])):
        yield rshift(shape, right)


def scroll(shape, wrap=True):
    shape = deepcopy(shape)
    width = len(shape[0])
    for i in range(width):
        yield rshift(shape, i, wrap=wrap)


def fade(frames, target):
    for i in range(1, frames + 1):
        yield min(1, 1.0 / i + target)


def palette_hsl_mod(palette, parameter):
    if parameter == 0.0:
        return palette
    palette = deepcopy(palette)
    result = []
    for color in palette:
        intensity = color[0] / 255.0
        c = Color(color)
        h, s, l, _ = c.hsla
        h = 360.0 * (parameter / 100.0)
        s = 100.0
        l = 50.0 * intensity
        c.hsla = (h, s, l)
        result.append(c.rgb)
    return result


def to_rgb(shape, palette, fade=1):
    shape = deepcopy(shape)
    return [
        [palette[int(pix)] for pix in line]
        for line in shape.strip().split("\n")
    ]


def to_pixerator(shape):
    shape = deepcopy(shape)
    for y, line in enumerate(shape):
        for x, pix in enumerate(line):
            yield x, y, pix


def draw(s, shape, palette=None, fade=1):
    shape = deepcopy(shape)
    for x, y, pix in to_pixerator(shape):
        s.set_at((x, y), pix)


def alpha_blend(img, back):
    # alpha*(img-back) + back
    result = []
    for i, pix in enumerate(img):
        backpix = back[i]
        r, g, b, a = pix
        alpha = 255.0 / a
        br, bg, bb, _ = backpix
        result.append(
            (alpha * (r - br) + br),
            (alpha * (g - bg) + bg),
            (alpha * (b - bb) + bb),
        )
    return result
