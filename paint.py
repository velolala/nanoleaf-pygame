import signal
import sys
from itertools import chain, repeat
from time import sleep

import pygame as pg
from nanoleafapi.nanoleaf import NanoleafConnectionError
from pygame import Surface

from canvas_monitor import COLORS, DEPTH, Nanoleaf, NanoleafDual
from draw import (center, dissolve, draw, dshift, lshift, rshift, scroll_in,
                  ushift)
from shapes import HEART, cloud1, cloud2, cloud3, flash_r


def signal_handler(sig, frame):
    display.close()
    pg.quit()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

color = COLORS[1]

pg.init()

# display = NanoleafDisplaySimulator((12, 6), hello=False)
nl = None
try:
    nl = Nanoleaf("192.168.178.214")
except NanoleafConnectionError:
    pass
dual = NanoleafDual(nl, hello=False)
display = dual.simulator

win = dual.set_mode((12, 6), 0, DEPTH)


def save(win: Surface, out=True):
    pixels = []
    _x, _y = win.get_size()

    for y in range(_y):
        pixels.append([
            win.get_at((x, y)) for x in range(_x)
        ])
    result = ""
    result += "\n".join(
        "".join(f"{COLORS.index(p[:3])}" for p in row)
        for row in pixels
    )
    if out:
        print(f'"""\n{result}\n"""')
    return result


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
            # drawn_color = win.get_at((x, y))
            # if drawn_color != _color:
            #     COLORS[COLORS.index(_color)] = drawn_color
            #     _color = drawn_color
        if event.type == pg.KEYDOWN and pg.key.get_focused():
            k, m = event.key, event.mod
            if m == 64:
                if k == 99:
                    # Ctrl+C(lear)
                    win.fill("black")
                if k == 119:
                    # Ctrl+W(rite)
                    save(dual.canvas.window)
                if k == 113:
                    # Ctrl+Q(uit)
                    signal_handler(None, None)
            else:
                if k == pg.K_LEFT:
                    shape = save(dual.canvas.window, out=False)
                    win.fill("black")
                    draw(win, lshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_RIGHT:
                    shape = save(dual.canvas.window, out=False)
                    win.fill("black")
                    draw(win, rshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_UP:
                    shape = save(dual.canvas.window, out=False)
                    win.fill("black")
                    draw(win, ushift(shape, 1, wrap=True), COLORS)
                if k == pg.K_DOWN:
                    shape = save(dual.canvas.window, out=False)
                    win.fill("black")
                    draw(win, dshift(shape, 1, wrap=True), COLORS)
                if k == 99:
                    # C(enter)
                    shape = save(dual.simulator.window)
                    win.fill("black")
                    draw(win, center(shape), COLORS)
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
                    pg.display.set_mode(
                        dual.simulator._screen.get_size(),
                        flags
                    )
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
