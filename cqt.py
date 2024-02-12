import time
import io
import sounddevice as sd
import librosa
import numpy as np
from queue import Empty, Queue

sr_44 = 48000
sr_22 = 22500
block_duration = 24
device = "USB Audio Device:"
window = 16000 * 1  # // 1

FMIN = librosa.note_to_hz("C1")


def generate_callback(qu: Queue, _gain: Queue):
    try:
        gain = _gain.get_nowait()
        gain *= 2
    except Empty:
        gain = 100

    def callback(indata, frames, time, status):
        nonlocal gain
        if status:
            text = " " + str(status) + " "
            print(text)
        try:
            gain = _gain.get_nowait()
            gain *= 2
        except Empty:
            pass
        if any(indata):
            indata.shape = (frames,)
            qu.put_nowait((indata, gain))

    return callback


def calc_cqt(y, gain, sr=sr_44, harm=True):
    start = time.monotonic()
    harm_y = librosa.effects.harmonic(y, margin=8)
    C_harm = np.abs(
        librosa.cqt(
            harm_y,
            sr=sr,
            fmin=FMIN,
            bins_per_octave=12,
            n_bins=12 * 6,
        )
    )

    # C = np.minimum(
    #    C_harm,
    #    librosa.decompose.nn_filter(
    #        C_harm, aggregate=np.median, metric="cosine"
    #    ),
    # )
    C = C_harm
    samples = len(C[0])
    displaywindow = 10

    if samples >= displaywindow:
        C = np.average(np.rot90(np.rot90(C)[:displaywindow], k=-1), axis=1)
    else:
        C = np.average(C, axis=1)
    maxis = librosa.util.localmax(C)
    mul = np.array([1.9 if maxis[_] else 0.9 for _ in range(len(maxis))])
    before = C[0]
    C = mul * C
    after = C[0]
    # print(maxis, len(C), before, after)
    # P = C / np.linalg.norm(C)
    # P = P * (1 / np.max(P))
    # gain = GAIN
    P = C * gain
    P = 9 * P  # palette width
    P = np.clip(P, 0, 9)
    I = P.astype(np.int8)
    I = I.reshape(6, 12)
    I = np.flip(I, axis=0)
    shape = io.StringIO()
    np.savetxt(shape, I, fmt="%s", delimiter="")
    shape = shape.getvalue()
    # print(time.monotonic() - start)
    return shape


def main(gain=15):
    qu = Queue(60)
    with sd.InputStream(
        device=device,
        channels=1,
        callback=generate_callback(qu, _gain=gain),
        blocksize=int(sr_44 * block_duration / 1000),
        samplerate=sr_44,
    ):
        data = np.empty((0, 0))
        while True:
            time.sleep(0.1)
            p = None
            while not qu.empty():
                try:
                    p = qu.get()
                    indata, gain = p
                    data = np.append(data, indata)
                except Empty:
                    pass
            if len(data) > 2000:
                # discard some
                # print(len(data))
                shape = calc_cqt(data, gain)
                data = data[-window:]
                yield shape
