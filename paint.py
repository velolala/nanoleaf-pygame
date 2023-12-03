import sys
import signal
from time import sleep
from itertools import repeat, chain
import pygame as pg
from pygame import Surface
from canvas_monitor import (
    Nanoleaf,
    NanoleafDual,
    COLORS,
)
from shapes import cloud1, cloud2, cloud3, flash_r, HEART
from draw import center, draw, dissolve, scroll_in, lshift


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
            if event.button == 1:
                _color = color
            if event.button == 3:
                _color = COLORS[0]
            (_x, _y) = pg.mouse.get_pos()
            s = display.scale
            x, y = _x // s, _y // s
            pg.draw.rect(win, _color, (x, y, 1, 1))
        if event.type == pg.KEYDOWN and pg.key.get_focused():
            k, m = event.key, event.mod
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
            if k == 112:
                # P(lay) something
                draw(win, center(HEART), COLORS)
                dual.flip()
                sleep(1)
                flash_l = lshift(flash_r, 6)
                for i in range(30):
                    if i % 2 == 0:
                        draw(win, flash_r, COLORS)
                    else:
                        draw(win, flash_l, COLORS)
                    dual.flip()
                    sleep(.007)
                    win.fill("black")
                    dual.flip()
                    sleep(.03)
                for frame in chain(*repeat(scroll_in(HEART), 5)):
                    draw(win, frame, COLORS)
                    dual.flip()
                    sleep(.3)
                frames = [cloud1, cloud2, cloud3]
                for i in range(len(frames) * 10):
                    draw(win, frames[i % len(frames)], COLORS)
                    dual.flip()
                    sleep(.07)
                for frame in dissolve(HEART):
                    draw(win, frame, COLORS)
                    dual.flip()
                    sleep(.1)

        dual.flip()
