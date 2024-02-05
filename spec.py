#!/usr/bin/env python3
"""Show a text-mode spectrogram using live microphone data."""
import sys
import math
import shutil
from collections import deque

import numpy as np
import sounddevice as sd
from queue import Queue, Empty, Full

device = 0

block_duration = 22  # block size ms
gain = 1250

octaves = 4
low, high = 55, 55 * 2**octaves
columns = 12 * octaves

# Create a nice output gradient using ANSI escape sequences.
# Stolen from https://gist.github.com/maurisvh/df919538bcef391bc89f
colors = 30, 34, 35, 91, 93, 97
chars = " :%#\t#%:"
gradient = []
for bg, fg in zip(colors, colors[1:]):
    for char in chars:
        if char == "\t":
            bg, fg = fg, bg
        else:
            gradient.append(f"\x1b[{fg};{bg + 10}m{char}")

samplerate = sd.query_devices(device, "input")["default_samplerate"]

delta_f = (high - low) / (columns - 1)
fftsize = math.ceil(samplerate / delta_f)
low_bin = math.floor(low / delta_f)


def generate_callback(qu: Queue):
    def callback(indata, frames, time, status):
        if status:
            text = " " + str(status) + " "
            print(text)
        if any(indata):
            magnitude = np.abs(np.fft.rfft(indata[:, 0], n=fftsize))
            magnitude *= gain / fftsize
            _line = [
                int(np.clip(x, 0, 9))
                for x in magnitude[low_bin : low_bin + columns]
            ]
            div = int(columns / 12)
            __line = [0] * 12
            for j in range(div):
                subline = list(_line)[j : j + 12]
                for i, val in enumerate(subline):
                    __line[i] += val
            _line = (str(min(9, val)) for val in __line)
            # line = (
            #     gradient[int(np.clip(x, 0, 1) * (len(gradient) - 1))]
            #     for x in magnitude[low_bin : low_bin + columns]
            # )
            try:
                qu.put_nowait("".join(_line))
            except Full:
                pass
        else:
            pass

    return callback


def main():
    qu = Queue(60)
    out = deque(maxlen=6)
    with sd.InputStream(
        device=device,
        channels=1,
        callback=generate_callback(qu),
        blocksize=int(samplerate * block_duration / 1000),
        samplerate=samplerate,
    ):
        while True:
            p = None
            try:
                p = qu.get()
                out.append(p)
            except Empty:
                p = None
            if p is not None:
                yield "\n".join(out).strip("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Interrupted by user")
    except Exception as e:
        sys.exit(type(e).__name__ + ": " + str(e))
