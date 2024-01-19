import signal
import sys
from itertools import chain, repeat

import pygame as pg
from nanoleafapi.nanoleaf import NanoleafConnectionError
from pygame import Surface
from rtmidi.midiutil import open_midiinput
from mido.messages.decode import decode_message

from canvas_monitor import COLORS, DEPTH, Nanoleaf, NanoleafDual
from draw import (bounce, center, dissolve, draw, dshift, lshift, rshift,
                  scroll, scroll_in, ushift)
from shapes import (HEART, blackout, cloud1, cloudrain, flash_r, love, velo,
                    wave, doggo, doggo2)


def signal_handler(sig, frame):
    display.close()
    close_midi()
    pg.quit()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

color = COLORS[1]
WIDTH, HEIGHT = (12, 6)
FILL = COLORS[0]


class MidiRecv:
    def __init__(self):
        self.controller_state = dict()
        self.speed_x = 0
        self.speed_y = 0
        self.fill_r = 0
        self.fill_g = 0
        self.fill_b = 0

    def get_speed(self):
        return (self.speed_x, self.speed_y)

    def get_fill(self):
        return (self.fill_r, self.fill_g, self.fill_b)

    def __call__(self, event, data=None):
        msg, what = event
        content = decode_message(msg)
        if content["control"] == 14:
            # max speed should be [-0.0555555, 0.05555555]
            self.speed_x = -(63 - content["value"]) / 63 * .05
        if content["control"] == 15:
            self.speed_y = -(63 - content["value"]) / 63 * .05
        if content["control"] == 0:
            self.fill_r = content["value"] / 127. * 255
        if content["control"] == 1:
            self.fill_g = content["value"] / 127. * 255
        if content["control"] == 2:
            self.fill_b = content["value"] / 127. * 255


midi = MidiRecv()


def install_midi():
    m_in, port_name = open_midiinput(1)  # FIXME: hardcoded port
    print(port_name)
    m_in.set_callback(midi)
    m_in.ignore_types(timing=False)
    return m_in


def close_midi():
    m_in.close_port()


pg.init()
m_in = install_midi()

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


def movie():
    factor = int(FPS / 6)
    dog = [doggo] * factor + [doggo2] * factor
    framescount = FPS * 12
    target = 0.0
    fadestep = (1. - target) / framescount
    for i in range():
        pic = dog[i % len(dog)]
        fade = 1 - (i * fadestep)
        yield rshift(pic, (i // factor) % WIDTH, wrap=True), fade

    for i in range(3 * FPS):
        if i % 12 < 2:
            yield blackout
        elif i < FPS:
            yield velo
        elif i < 2 * FPS:
            yield rshift(velo, int((i - FPS) // (FPS/6.)), wrap=True)
        else:
            yield love

    for _ in range(FPS):
        yield center(HEART)

    flash_l = lshift(flash_r, 6)
    for i in range(30):
        if i % 8 < 5:
            yield flash_r
        else:
            yield flash_l
    for frame in list(
        chain(*repeat(list(scroll_in(HEART)), 2))
    )[:-9]:
        yield from repeat(frame, FPS // 5)

    for frame in dissolve(center(HEART)):
        yield from repeat(frame, FPS // 5)
    for frame in list(scroll_in(center(cloud1)))[:-11]:
        yield from repeat(frame, FPS // 5)
    for frame in chain(*repeat(cloudrain, 3)):
        yield from repeat(frame, FPS // 10)
    for frame in chain(*repeat(list(scroll(wave)), FPS // 20)):
        yield from repeat(frame, FPS // 40)
    yield blackout


flags = dual.simulator._screen.get_flags()
clock = pg.Clock()
speed_x = speed_y = 0
moved_x = moved_y = 0
frame = frames = None
_prev_shape = None
_prev_acceleration = None
FPS = 120
ACCEL = .001
while True:
    dt = clock.tick(FPS)
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
            if m == pg.KMOD_LCTRL:
                if k == pg.K_c:
                    # Ctrl+C(lear)
                    win.fill(FILL)
                    speed_x = speed_y = 0
                if k == pg.K_w:
                    # Ctrl+W(rite)
                    save(dual.simulator.window)
                if k == pg.K_q:
                    # Ctrl+Q(uit)
                    signal_handler(None, None)
                if k == pg.K_LEFT:
                    speed_x -= ACCEL
                if k == pg.K_RIGHT:
                    speed_x += ACCEL
                if k == pg.K_UP:
                    speed_y += ACCEL
                if k == pg.K_DOWN:
                    speed_y -= ACCEL
                if k == pg.K_b:
                    # Ctrl+B(ounce)
                    shape = save(dual.simulator.window, out=False)
                    _prev_shape = shape
                    _prev_acceleration = speed_x, moved_x, speed_y, moved_y
                    frames = bounce(shape, FPS // 20)
            else:
                if k == pg.K_LEFT:
                    shape = save(dual.simulator.window, out=False)
                    win.fill(FILL)
                    draw(win, lshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_RIGHT:
                    shape = save(dual.simulator.window, out=False)
                    win.fill(FILL)
                    draw(win, rshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_UP:
                    shape = save(dual.simulator.window, out=False)
                    win.fill(FILL)
                    draw(win, ushift(shape, 1, wrap=True), COLORS)
                if k == pg.K_DOWN:
                    shape = save(dual.simulator.window, out=False)
                    win.fill(FILL)
                    draw(win, dshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_c:
                    # C(enter)
                    shape = save(dual.simulator.window, out=False)
                    win.fill(FILL)
                    draw(win, center(shape), COLORS)
                if k == pg.K_b:
                    # B(lack)
                    color = COLORS[0]
                if k == pg.K_n:
                    # N(ext color)
                    color = COLORS[(COLORS.index(color) + 1) % len(COLORS)]
                if k == pg.K_f:
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
                if k == pg.K_p:
                    # P(lay) something
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = movie()
    fade = 1
    if frames is not None:
        try:
            frame, fade = next(frames)
            speed_x = speed_y = moved_x = moved_y = 0
        except StopIteration:
            frame = None
            frames = None
            draw(dual.simulator.window, _prev_shape, COLORS)
            if _prev_acceleration is not None:
                speed_x, moved_x, speed_y, moved_y = _prev_acceleration

    if frame is not None:
        shape = frame
    else:
        shape = save(dual.simulator.window, out=False)
    win.fill(FILL)
    speed_x, speed_y = midi.get_speed()

    move_x = speed_x * max(1, dt)
    move_y = speed_y * max(1, dt)
    moved_x += move_x
    moved_y += move_y
    # print(speed_x, move_x, moved_x, speed_y, move_y, moved_y, dt)
    if moved_x >= 1:
        shape = rshift(shape, int(moved_x), wrap=True)
    elif moved_x <= -1:
        shape = lshift(shape, -int(moved_x), wrap=True)
    if moved_y >= 1:
        shape = ushift(shape, int(moved_y), wrap=True)
    elif moved_y <= -1:
        shape = dshift(shape, - int(moved_y), wrap=True)
    moved_x -= int(moved_x)
    moved_y -= int(moved_y)
    draw(win, shape, COLORS, fade=fade)
    dual.flip()
