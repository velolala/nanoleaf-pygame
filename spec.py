#!/usr/bin/env python3
"""Show a text-mode spectrogram using live microphone data."""
import sys
import math
import shutil
from collections import deque

import numpy as np
import sounddevice as sd
from queue import Queue, Empty, Full

device = "USB PnP"

block_duration = 22  # block size ms

octaves = 4
low, high = 55, 55 * 2**octaves
columns = 12 * octaves

samplerate = sd.query_devices(device, "input")["default_samplerate"]

delta_f = (high - low) / (columns - 1)
fftsize = math.ceil(samplerate / delta_f)
low_bin = math.floor(low / delta_f)


def generate_callback(qu: Queue, _gain: Queue):
    gain = 1250
    try:
        gain = _gain.get_nowait()
    except Empty:
        pass

    def callback(indata, frames, time, status):
        nonlocal gain
        if status:
            text = " " + str(status) + " "
            print(text)
        try:
            gain = _gain.get_nowait()
        except Empty:
            pass
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
            try:
                qu.put_nowait("".join(_line))
            except Full:
                pass
        else:
            pass

    return callback


def main(gain):
    qu = Queue(60)
    out = deque(maxlen=6)
    with sd.InputStream(
        device=device,
        channels=1,
        callback=generate_callback(qu, _gain=gain),
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
