import pygame as pg
import sys
import signal
from canvas_monitor import Nanoleaf, NanoleafDisplay, NanoleafDisplaySimulator
from nanoleafapi import NanoleafConnectionError
from time import sleep
import random


def signal_handler(sig, frame):
    display.close()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

display = None
try:
    nl = Nanoleaf("192.168.178.214")
    display = NanoleafDisplay(nl)
except NanoleafConnectionError:
    display = NanoleafDisplaySimulator((12, 6), hello=False)


window = display.set_mode((12, 6), 0, 16)
s = window.copy()
s.fill("black")
s.set_colorkey("black")


def surface_rotate(s):
    red = s.copy()
    pg.draw.line(red, "red", (0, 0), (12, 6), width=2)
    green = s.copy()
    pg.draw.line(green, "green", (0, 0), (12, 6), width=2)
    yellow = s.copy()
    pg.draw.line(yellow, "yellow", (0, 0), (12, 6), width=2)

    line = red

    angle = 0
    d_angle = 1
    scroll = 0
    direction = 1
    while True:
        if random.random() > .99:
            direction = random.choice((-1, 1))
        d_angle += direction
        line = random.choice((red, green, yellow))
        angle = (angle + (d_angle * direction)) % 360
        scroll = (scroll + 1) % 12
        sleep(.005)
        s.fill("black")
        s = pg.transform.rotate(line, angle)
        x = int((s.get_width() - 12) / 2 + .5)
        y = int((s.get_height() - 6) / 2 + .5)
        print(x, y, s.get_size())
        viewport = s.subsurface((x, y, 12, 6))
        window.blit(viewport, (0, 0))
        display.flip()


def position_rotate(s):
    sx, sy, ex, ey = (0, 0, 12, 6)
    while True:
        line = s.copy()
        pg.draw.line(line, "red", (sx, sy), (ex, ey), width=2)
        window.blit(line, (0, 0))
        display.flip()
        sleep(.5)
        sx = (sx + 1) % 12
        sy = (sy + 1) % 6
        ex = (ex + 1)
        ey = (ey + 1)


def ball_test():
    size = 0
    s = pg.Surface((1200, 600), 0, 16)

    while True:
        s.fill("black")
        size += 10
        size = size % int(s.get_width() / 2 + 1)
        pg.draw.circle(
            s,
            random.choice(("green", "blue", "red")),
            (int(s.get_width() / 2), int(s.get_height() / 2)),
            size
        )
        s = pg.transform.box_blur(s, 1)
        view = pg.transform.scale(s, (12, 6))
        window.blit(view, (0, 0))
        display.flip()
        sleep(.02)


# surface_rotate(s)
# position_rotate(s)
ball_test()
