from nanoleafapi import Nanoleaf
from time import sleep
from pygame import Surface
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


class NanoleafDisplay():

    def __init__(self, nl: Nanoleaf, hello=True):

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
        if hello:
            self.hello()

    def hello(self):
        colors = (
            BLACK, RED, ORANGE, YELLOW, GREEN,
            LIGHT_BLUE, BLUE, PINK, PURPLE, WHITE,
        )
        for step in range(len(self.panel_ids)):
            frame_data = [
                colors[(step + i) % len(colors)]
                for i in range(len(self.panel_ids))
            ]
            self.draw_frame(frame_data)
            sleep(3. / len(self.panel_ids))
        self.draw_frame([BLACK for _ in range(len(self.panel_ids))])

    def close(self):
        self.nanoleaf_socket.close()

    def blit(self, s: Surface):
        pixels = []
        for y in range(s.get_height()):
            pixels.extend([s.get_at((x, y))[:3] for x in range(s.get_width())])
        self.draw_frame(pixels)

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
