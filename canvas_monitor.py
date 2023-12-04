from nanoleafapi import Nanoleaf
from math import prod
from typing import Tuple
from time import sleep
import pygame as pg
from pygame import Rect, Surface
import socket
from nanoleafapi import (
    RED,
    ORANGE,
    YELLOW,
    GREEN,
    LIGHT_BLUE,
    BLUE,
    PINK,
    PURPLE,
    WHITE,
)

BLACK = (0, 0, 0)

nanoleaf_host = '192.168.178.214'
NANOLEAF_UDP_PORT = 60222

COLORS = [
    BLACK,
    RED,
    ORANGE,
    YELLOW,
    GREEN,
    LIGHT_BLUE,
    BLUE,
    PINK,
    PURPLE,
    WHITE,
]


DEPTH = 32


class NanoleafDisplay():

    def __init__(self, nl: Nanoleaf, hello=True):
        if nl is not None:
            self.nanoleaf_socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, 0
            )
            self.nl = nl

            panels = self.nl.get_layout()["positionData"]
            panels = sorted(panels, key=lambda p: (-p['y'], p['x']))
            self.panel_ids = [p["panelId"] for p in panels]
            n_panels = len(self.panel_ids)

            self.n_panels_b = n_panels.to_bytes(2, "big")
            self.nl.enable_extcontrol()

            self.window = Surface(
                (
                    (len(set(p["x"] for p in panels))),
                    (len(set(p["y"] for p in panels))),
                ), 0, DEPTH
            )
            if hello:
                self.hello()

    def hello(self):
        for step in range(len(self.panel_ids)):
            frame_data = [
                COLORS[(step + i) % len(COLORS)]
                for i in range(len(self.panel_ids))
            ]
            self.draw_frame(frame_data)
            sleep(3. / len(self.panel_ids))
        self.draw_frame([BLACK for _ in range(len(self.panel_ids))])

    def close(self):
        self.nanoleaf_socket.close()

    def set_mode(self, geometry: Tuple[int, int], *args, **kwargs) -> Surface:
        print(f"ignoring {args} and {kwargs}")
        assert geometry == self.window.get_size()
        return self.window

    def update(self, rect: Rect):
        pixels = []
        for y in range(self.window.get_height()):
            pixels.extend(
                [
                    self.window.get_at((x, y))[:3]
                    for x in range(self.window.get_width())
                ]
            )
        self.draw_frame(pixels)

    def flip(self):
        self.update(Rect((0, 0), self.window.get_size()))

    def draw_frame(self, frame_data):
        transition = 0
        assert len(frame_data) == len(self.panel_ids), (
            len(frame_data), len(self.panel_ids)
        )

        send_data = b""
        send_data += self.n_panels_b

        for count, pixelrgb in enumerate(frame_data):
            panel_id = self.panel_ids[count]
            red, green, blue = pixelrgb
            panel_id_b = panel_id.to_bytes(2, "big")
            send_data += panel_id_b
            send_data += red.to_bytes(1, "big")
            send_data += green.to_bytes(1, "big")
            send_data += blue.to_bytes(1, "big")
            white = 0
            send_data += white.to_bytes(1, "big")
            send_data += transition.to_bytes(2, "big")

        self.nanoleaf_socket.sendto(
            send_data, (self.nl.ip, NANOLEAF_UDP_PORT)
        )


class NanoleafDisplaySimulator(NanoleafDisplay):

    def __init__(self, geometry, scale=40, hello=True):
        width, height = geometry
        self._screen = pg.display.set_mode(
            (width * scale, height * scale),
            pg.DOUBLEBUF, DEPTH
        )
        self.window = Surface(geometry, 0, DEPTH)
        self.scale = scale
        if hello:
            self.hello()
        super().__init__(None, hello=False)

    def update(self, rect: Rect):
        scaled = pg.transform.scale(
            self.window.copy(),
            self._screen.get_size(),
        )
        self._screen.blit(scaled, (0, 0))
        pg.display.update(rect)

    def flip(self):
        self.update(Rect((0, 0), self._screen.get_size()))

    def hello(self):
        for step in range(prod(self.window.get_size())):
            i = 0
            for y in range(self.window.get_height()):
                for x in range(self.window.get_width()):
                    self.window.set_at(
                        (x, y),
                        COLORS[(step + i) % len(COLORS)]
                    )
                    i += 1
            self.flip()
            sleep(3. / prod(self.window.get_size()))
        self.window.fill(BLACK)
        self.flip()

    def close(self):
        pg.quit()


class NanoleafDual():

    def __init__(self, nl, scale=120, hello=True):
        if nl is not None:
            self.canvas = NanoleafDisplay(nl, hello=hello)
            self.dimensions = self.canvas.window.get_size()
        else:
            # FIXME: hardcoded dimensions
            self.dimensions = (12, 6)
            self.canvas = None
        self.simulator = NanoleafDisplaySimulator(
            self.dimensions,
            scale=scale,
            hello=hello
        )

    def close(self):
        if self.canvas is not None:
            self.canvas.quit()
        self.simulator.quit()

    def update(self, rect):
        if self.canvas is not None:
            self.canvas.window = self.simulator.window.copy()
            self.canvas.update(rect)
        self.simulator.update(rect)

    def set_mode(self, *args, **kwargs):
        return self.simulator.set_mode(*args, **kwargs)

    def flip(self):
        self.update(Rect((0, 0), self.simulator._screen.get_size()))
