from itertools import chain, repeat


def rshift(shape, i, wrap=False):
    lines = shape.strip().split("\n")
    if i == 0:
        return shape
    if wrap:
        return "\n".join(
            line[-i:] + line[:-i] for line in lines
        )
    else:
        return "\n".join(
            i * "0" + line[:-i] for line in lines
        )


def lshift(shape, i, wrap=False):
    lines = shape.strip().split("\n")
    if wrap:
        return "\n".join(
            line[i:] + line[:-i] for line in lines
        )
    else:
        return "\n".join(
            line[i:] + "0" * i for line in lines
        )


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
    lines = shape.strip().split("\n")
    if wrap:
        return "\n".join(
            lines[i:] + lines[:i]
        )
    return "\n".join(
        lines[i:] + ["0" * len(lines[0]) for _ in range(i)]
    )


def dshift(shape, i, wrap=False):
    lines = shape.strip().split("\n")
    if wrap:
        return "\n".join(
            lines[-i:] + lines[:len(lines) - i]
        )
    return "\n".join(
        ["0" * len(lines[0]) for _ in range(i)] + lines[:-i]
    )


def scroll(shape):
    width = len(shape.strip().split("\n")[0])
    for i in range(width):
        yield rshift(shape, i)
    for i in range(width):
        yield lshift(shape, i)


def dissolve(shape):
    lines = shape.strip().split("\n")
    yield shape
    for i in range(len(lines[0])):
        yield "\n".join(
            chain(
                lshift(shape, i).split("\n")[:len(lines) // 2],
                rshift(shape, i).split("\n")[len(lines) // 2:],
            )
        )


def all_zero(lines):
    count = 0
    while all(all(p == "0" for p in line[:count]) for line in lines):
        count += 1
    return count


def center(shape):
    lines = shape.strip().split("\n")
    pre = all_zero(lines)
    suf = all_zero([line[::-1] for line in lines])
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
    lines = shape.strip().split("\n")

    for left in range(all_zero([line[::-1] for line in lines]), 0, -1):
        yield lshift(shape, left)
    for right in range(0, len(lines[0])):
        yield rshift(shape, right)


def draw(s, shape, palette):
    for y, pix in enumerate(shape.strip().split("\n")):
        for x, i in enumerate(pix):
            s.set_at((x, y), palette[int(i)])
