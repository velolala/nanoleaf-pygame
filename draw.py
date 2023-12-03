from itertools import chain


def rshift(shape, i):
    return "\n".join(i * "0" + pix[:-i] for pix in shape.strip().split("\n"))


def lshift(shape, i):
    return "\n".join(pix[i:] + "0" * i for pix in shape.strip().split("\n"))


def scroll(shape):
    for i in range(len(shape.strip().split("\n")[0])):
        yield rshift(shape, i)
    for i in range(len(shape.strip().split("\n")[0])):
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
    if pre < margin:
        return rshift(shape, margin - pre)
    if suf < margin:
        return lshift(shape, margin - pre)


def scroll_in(shape):
    lines = shape.strip().split("\n")

    for left in range(all_zero([line[::-1] for line in lines]) + 1, 0, -1):
        yield lshift(shape, left)
    for right in range(1, len(lines[0])):
        yield rshift(shape, right)


def draw(s, shape, palette):
    for y, pix in enumerate(shape.strip().split("\n")):
        for x, i in enumerate(pix):
            s.set_at((x, y), palette[int(i)])
