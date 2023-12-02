import sys
import signal
import pygame as pg
from pygame import Surface
from canvas_monitor import (
    Nanoleaf,
    NanoleafDual,
    COLORS,
)


def signal_handler(sig, frame):
    display.close()
    pg.quit()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

color = COLORS[1]

pg.init()

# display = NanoleafDisplaySimulator((12, 6), hello=False)
nl = Nanoleaf("192.168.178.214")
dual = NanoleafDual(nl, hello=False)
display = dual.simulator

win = dual.set_mode((12, 6), 0, 16)


def save(win: Surface):
    pixels = []
    _x, _y = win.get_size()
    for y in range(_y):
        pixels.append([
            win.get_at((x, y)) for x in range(_x)
        ])
    print('"""')
    print(
        "\n".join(
            "".join(f"{COLORS.index(p[:3])}" for p in row)
            for row in pixels
        )
    )
    print('"""')


flags = dual.simulator._screen.get_flags()


while True:
    for event in pg.event.get():
        if event.type == pg.MOUSEBUTTONDOWN:
            (_x, _y) = pg.mouse.get_pos()
            s = display.scale
            x, y = _x // s, _y // s
            pg.draw.rect(win, color, (x, y, 1, 1))
        if event.type == pg.KEYDOWN and pg.key.get_focused():
            k, m = event.key, event.mod
            print(k)
            if k == 99 and m == 64:
                # Ctrl+C(lear)
                win.fill("black")
            if k == 119 and m == 64:
                # Ctrl+W(rite)
                save(dual.canvas.window)
            if k == 113 and m == 64:
                # Ctrl+Q(uit)
                signal_handler(None, None)
            if k == 98:
                # B(lack)
                color = COLORS[0]
            if k == 110:
                # N(ext color)
                color = COLORS[(COLORS.index(color) + 1) % len(COLORS)]
            if k == 102:
                # F(ullscreen toggle)
                if flags & pg.FULLSCREEN is False:
                    flags |= pg.FULLSCREEN
                else:
                    flags ^= pg.FULLSCREEN
                print(flags)
                pg.display.set_mode(dual.simulator._screen.get_size(), flags)

        dual.flip()
