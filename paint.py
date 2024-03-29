import signal
import sys
from itertools import chain, cycle, repeat
from copy import deepcopy
import random
from queue import Queue

import pygame as pg

from nanoleafapi.nanoleaf import NanoleafConnectionError
from pygame import Color, Surface
from rtmidi.midiutil import open_midiinput, open_midioutput
from mido.messages.decode import decode_message
from mido import Message
from anim import RandomAnim
from clock import now, fadeout
import spec
import cqt
import beatomator as beat

from osci import SineOscillator
from canvas_monitor import COLORS, DEPTH, Nanoleaf, NanoleafDual
from draw import (
    bounce,
    center,
    color_to_shape,
    dissolve,
    draw,
    dshift,
    keyblend,
    lshift,
    palette_hsl_mod,
    rshift,
    scroll,
    scroll_in,
    swap,
    to_rgb,
    ushift,
)
from shapes import (
    HEART,
    blackout,
    cloud1,
    cloudrain,
    flash_r,
    love,
    velo,
    wave,
    doggo,
    doggo2,
)
from colors import whites


pg.init()


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
    def __init__(self, out, tick_fn):
        self.out = out
        self.tick = tick_fn
        self.controller_state = dict()
        self.speed_x = 0
        self.speed_y = 0
        self.fill_r = 9
        self.fill_g = 9
        self.fill_b = 9
        self.fill_set = False
        self.front_col = 0.0
        self._gain = Queue(10)
        self._gain.put(50)
        self.scene = 0
        self.swap_h = False
        self.swap_v = False
        self.update_color_knobs("rgb")

    def get_speed(self):
        return (self.speed_x, self.speed_y)

    def get_fill(self):
        return tuple(map(int, (self.fill_r, self.fill_g, self.fill_b)))

    def _rgb_from_hsl(self):
        c = Color(0, 0, 0)
        c.hsla = (self.fill_h, self.fill_s, self.fill_l)
        self.fill_r, self.fill_g, self.fill_b, _ = c

    def _hsl_from_rgb(self):
        self.fill_h, self.fill_s, self.fill_l, _ = Color(
            self.fill_r, self.fill_g, self.fill_b
        ).hsla

    def update_color_knobs(self, origin):
        updates = []
        if origin == "rgb":
            self._hsl_from_rgb()
            updates = [
                (5, self.fill_h, 360),
                (6, self.fill_s, 100),
                (7, self.fill_l, 100),
            ]
        if origin == "hsl":
            self._rgb_from_hsl()
            updates = [
                (0, self.fill_r, 255),
                (1, self.fill_g, 255),
                (2, self.fill_b, 255),
            ]
        for control, value, range in updates:
            self.out.send_message(
                Message(
                    "control_change",
                    channel=12,
                    control=control,
                    value=int(value / range * 127.0 + 0.5),
                ).bytes()
            )

    def __call__(self, event, data=None):
        msg, what = event
        content = decode_message(msg)
        if content["type"] == "clock":
            self.tick()
        # R/G/B
        if content["control"] == 0:
            self.fill_r = content["value"] / 127.0 * 255
            self.update_color_knobs("rgb")
            self.fill_set = True
        if content["control"] == 1:
            self.fill_g = content["value"] / 127.0 * 255
            self.update_color_knobs("rgb")
            self.fill_set = True
        if content["control"] == 2:
            self.fill_b = content["value"] / 127.0 * 255
            self.update_color_knobs("rgb")
            self.fill_set = True
        # gain
        if content["control"] == 3:
            self._gain.put(content["value"])
        # H/S/L
        if content["control"] == 5:
            self.fill_h = content["value"] / 127.0 * 360
            self.update_color_knobs("hsl")
            self.fill_set = True
        if content["control"] == 6:
            self.fill_s = content["value"] / 127.0 * 100
            self.update_color_knobs("hsl")
            self.fill_set = True
        if content["control"] == 7:
            self.fill_l = content["value"] / 127.0 * 100
            self.update_color_knobs("hsl")
            self.fill_set = True
        # Front parameter
        if content["control"] == 11:
            self.front_col = content["value"] / 127.0 * 100

        # speed X/Y
        if content["control"] == 14:
            # max speed should be [-0.0555555, 0.05555555]
            self.speed_x = -(63 - content["value"]) / 63 * 0.05
        if content["control"] == 15:
            self.speed_y = -(63 - content["value"]) / 63 * 0.05

        if content["control"] == 20 and content["value"] == 0:
            self.swap_h = not self.swap_h

        if content["control"] == 24 and content["value"] == 0:
            self.swap_v = not self.swap_v

        if content["control"] == 28 and content["value"] == 0:
            try:
                newevent = pg.event.Event(
                    pg.KEYDOWN,
                    unicode="z",
                    key=pg.K_z,
                    mod=pg.KMOD_NONE,
                )
                pg.event.post(newevent)  # add the event to the queue
            except Exception as ex:
                print(ex)

    def get_scene_change(self):
        pass


def install_midi(callback):
    m_in, port_name = open_midiinput(1)  # FIXME: hardcoded port
    print(port_name)
    m_in.set_callback(callback)
    m_in.ignore_types(timing=False)
    return m_in


def install_midi_out():
    m_out, port_name = open_midioutput(1)  # FIXME: hardcoded port
    print(port_name)
    return m_out


def close_midi():
    m_in.close_port()
    m_out.close_port()


def init_midi_controller(out):
    # RGB background
    for control in range(3):
        out.send_message(
            Message(
                "control_change", channel=12, control=control, value=9
            ).bytes()
        )
    # gain
    out.send_message(
        Message("control_change", channel=12, control=3, value=50).bytes()
    )
    # speed X
    out.send_message(
        Message("control_change", channel=12, control=14, value=63).bytes()
    )
    # speed Y
    out.send_message(
        Message("control_change", channel=12, control=15, value=63).bytes()
    )


beatomator = beat.Beatomator()
m_out = install_midi_out()
init_midi_controller(m_out)
midi = MidiRecv(m_out, beatomator.tick)
m_in = install_midi(midi)


def random_fillh(count):
    midi.fill_h = (midi.fill_h + 50) % 360
    midi.fill_s = 100.0
    midi._rgb_from_hsl()
    midi.fill_set = True


def random_front_col(count):
    midi.front_col = random.random() * 360


def desaturate(count):
    if count % (2 * beat.QUARTER) == 36:
        midi.fill_s = 100.0
    else:
        midi.fill_s = 50.0
    midi._rgb_from_hsl()
    midi.fill_set = True


beatomator.schedule(*beat.mk_phrase4(random_fillh))
beatomator.schedule(*beat.mk_beat(random_front_col))
beatomator.schedule(*beat.mk_offbeat(desaturate))


def save(win: Surface, out=True):
    pixels = []
    _x, _y = win.get_size()

    for y in range(_y):
        pixels.append([win.get_at((x, y)) for x in range(_x)])
    if out:
        result = ""
        result += "\n".join(  # if p != fill
            "".join(f"{COLORS.index(p[:3])}" for p in row) for row in pixels
        )
        if out:
            print(f'"""\n{result}\n"""')
    return pixels


# Screen setup
nl = None
try:
    nl = Nanoleaf("192.168.178.214")
except NanoleafConnectionError:
    pass
dual = NanoleafDual(nl, hello=False)
display = dual.simulator

win = dual.set_mode((WIDTH, HEIGHT), 0, DEPTH)

# Parameters
display_clock = False

flags = dual.simulator._screen.get_flags()
clock = pg.Clock()
speed_x = speed_y = 0
moved_x = moved_y = 0
frame = frames = None
_prev_shape = None
_prev_acceleration = None
FPS = 120
ACCEL = 0.001

shape = save(win, out=False)
fill = color_to_shape(shape, FILL)
lastfill = fill


def _clock():
    while display_clock is True:
        yield now()
    yield blackout


def _cqt():
    gen = cqt.main(midi._gain)
    count = 0
    move = rshift
    frame = velo
    while True:
        count += abs(midi.speed_x) * 10
        if midi.speed_x < 0:
            move = lshift
        else:
            move = rshift
        frame = next(gen) or frame
        palette = palette_hsl_mod(whites, midi.front_col)
        yield move(
            keyblend(
                to_rgb(frame, palette),
                color_to_shape(
                    [
                        [palette[0] for _ in range(WIDTH)]
                        for _ in range(HEIGHT)
                    ],  # empty frame
                    midi.get_fill(),
                ),
                key=palette[0],
            ),
            int(count / 8) % 12,
            wrap=True,
        )
    yield StopIteration


def _spec():
    gen = spec.main(midi._gain, smoothing=FPS // 10)
    count = 0
    move = rshift
    palette = whites
    frame = velo
    while True:
        count += abs(midi.speed_x) * 10
        if midi.speed_x < 0:
            move = lshift
        else:
            move = rshift
        frame = next(gen) or frame
        palette = palette_hsl_mod(whites, midi.front_col)
        yield move(
            keyblend(
                to_rgb(frame, palette),
                color_to_shape(
                    [
                        [palette[0] for _ in range(WIDTH)]
                        for _ in range(HEIGHT)
                    ],  # empty frame
                    midi.get_fill(),
                ),
                key=palette[0],
            ),
            int(count / 8) % 12,
            wrap=True,
        )
    yield StopIteration


sound2lights = cycle((_spec, _cqt))


def movie():
    osc = SineOscillator(FPS=FPS, freq=2, _min=0.3, _max=0.4)
    for f in _movie():
        yield fadeout(f[::], next(osc))


def _doggo():
    factor = int(FPS / 3)
    dog = [doggo] * factor + [doggo2] * factor
    for i in range(FPS * 5):
        pic = dog[i % len(dog)]
        yield rshift(pic, i // int(FPS / 3), wrap=True)


def _rain():
    for frame in list(scroll_in(center(cloud1)))[:-11]:
        yield from repeat(frame, FPS // 5)
    for frame in chain(*repeat(cloudrain, 3)):
        yield from repeat(frame, FPS // 10)


def _raindog():
    r = cycle(_rain())
    d = _doggo()
    try:
        while True:
            yield keyblend(next(r), next(d))
    except StopIteration:
        return


def _movie():
    for frame in _raindog():
        yield frame
    for i in range(3 * FPS):
        if i % 12 < 2:
            yield blackout
        elif i < FPS:
            yield velo
        elif i < 2 * FPS:
            yield rshift(velo, int((i - FPS) // (FPS / 6.0)), wrap=True)
        else:
            yield love

    for frame in _doggo():
        yield frame

    for _ in range(FPS):
        yield center(HEART)
    flash_l = lshift(flash_r, 6)
    for i in range(30):
        if i % 8 < 5:
            yield flash_r
        else:
            yield flash_l
    for frame in list(chain(*repeat(list(scroll_in(HEART)), 2)))[:-9]:
        yield from repeat(frame, FPS // 5)
    for frame in dissolve(center(HEART)):
        yield from repeat(frame, FPS // 5)
    for frame in _rain():
        yield frame
    for frame in chain(*repeat(list(scroll(wave)), FPS // 20)):
        yield from repeat(frame, FPS // 40)
    yield blackout


def counter():
    length = FPS / 12
    count = 0
    while count < 9999 * length + length:
        num = int(count // length)
        frame = now(military=f"{num:04}")
        count += 1
        yield frame
    yield blackout


assert shape is not None
assert len(shape) == 6
assert len(shape[0]) == 12


display_clock = not display_clock
frames = _cqt()

while True:
    dt = clock.tick(FPS)
    # [beatomator.tick() for _ in range(12)]
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
        if (
            event.type == pg.KEYDOWN
        ):  # and pg.key.get_focused(): # synthetic key events are not focussed
            k, m = event.key, event.mod
            if m == pg.KMOD_LCTRL:
                if k == pg.K_u:
                    display_clock = not display_clock
                    if display_clock:
                        _prev_shape = save(dual.simulator.window, out=False)
                        frames = _clock()
                if k == pg.K_t:
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = counter()
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
                if k == pg.K_t:
                    shape = now()
                    draw(win, shape)
                if k == pg.K_LEFT:
                    shape = save(dual.simulator.window, out=False)
                    # win.fill(FILL)
                    draw(win, lshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_RIGHT:
                    shape = save(dual.simulator.window, out=False)
                    # win.fill(FILL)
                    draw(win, rshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_UP:
                    shape = save(dual.simulator.window, out=False)
                    # win.fill(FILL)
                    draw(win, ushift(shape, 1, wrap=True), COLORS)
                if k == pg.K_DOWN:
                    shape = save(dual.simulator.window, out=False)
                    # win.fill(FILL)
                    draw(win, dshift(shape, 1, wrap=True), COLORS)
                if k == pg.K_c:
                    # C(enter)
                    shape = save(dual.simulator.window, out=False)
                    # win.fill(FILL)
                    draw(win, center(shape), COLORS)
                if k == pg.K_b:
                    # B(lack)
                    color = COLORS[0]
                if k == pg.K_q:
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = _cqt()
                if k == pg.K_s:
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = _spec()
                if k == pg.K_z:
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = next(sound2lights)()
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
                        dual.simulator._screen.get_size(), flags
                    )
                if k == pg.K_r:
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = RandomAnim(FPS)
                if k == pg.K_p:
                    # P(lay) something
                    _prev_shape = save(dual.simulator.window, out=False)
                    frames = movie()
    if frames is not None:
        try:
            frame = next(frames)
            speed_x = speed_y = moved_x = moved_y = 0
        except StopIteration:
            frame = None
            frames = None
            draw(dual.simulator.window, _prev_shape, COLORS)
            if _prev_acceleration is not None:
                speed_x, moved_x, speed_y, moved_y = _prev_acceleration

    if frame is not None and frame is not StopIteration:
        fill = COLORS[0]
        shape = frame[::]
        midi.fill_set = True
    else:
        shape = save(dual.simulator.window, out=False)
    # win.fill(FILL)
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
        shape = dshift(shape, -int(moved_y), wrap=True)
    moved_x -= int(moved_x)
    moved_y -= int(moved_y)
    if midi.fill_set:
        lastfill = fill
        fill = midi.get_fill()
        midi.fill_set = False
        shape = deepcopy(shape)
        shape = keyblend(shape, color_to_shape(shape, fill), key=lastfill)
    shape = swap(shape, v=midi.swap_v, h=midi.swap_h)

    draw(win, shape, COLORS)
    dual.flip()
