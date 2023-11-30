import pygame as pg
import sys
import signal
from canvas_monitor import RED, GREEN, BLACK, Nanoleaf, NanoleafDisplay
from time import sleep
import random

def signal_handler(sig, frame):
    display.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

nl = Nanoleaf("192.168.178.214")

display = NanoleafDisplay(nl)

s = pg.Surface((12, 6), 0, 16)
s.fill("black")
s.set_colorkey("black")


#viewport = s.subsurface((0, 3, 12, 6))
#print(viewport.get_size())
#display.blit(viewport)

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
       display.blit(viewport)

def position_rotate(s):
    angle = 0
    d_angle = 1
    scroll = 0
    direction = 1
    sx, sy, ex, ey = (0, 0, 12, 6)
    while True:
        line = s.copy()
        pg.draw.line(line, "red", (sx, sy), (ex, ey), width=2)
        display.blit(line)
        sleep(.5)
        sx = (sx + 1) % 12
        sy = (sy + 1) % 6
        ex = (ex + 1)
        ey = (ey + 1)


#surface_rotate(s)
position_rotate(s)
