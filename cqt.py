import time
import io
import sounddevice as sd
import librosa
import numpy as np
from queue import Empty, Queue

sr_44 = 48000
sr_22 = 22500
block_duration = 48
device = "USB Audio Device:"
# how fast we recalculate
update_interval = 0.001
# how much data we analyze
window = 16000 // 4  # // 1
# what does this do?
mindata = window // 16
# how many samples we average for display
displaywindow = 555
# how much we queue
q_len = 20
# scale gain
gain_divider = 100.0
# noise gate
gate_sum_threshold = 100
gate_abs_threshold = 0.2

FMIN = librosa.note_to_hz("C1")


def norm(x, r=(-1, 1)):
    # normalise x to range 'r', e.g. [-1,1]
    nom = (x - x.min()) * r[1] - r[0]
    denom = x.max() - x.min()
    return nom / denom + r[0]


def sigmoid(x, k=0.1):
    if k == 1.0:
        k = 0
    elif k == 0.0:
        k = 0.001
    # sigmoid function
    # use k to adjust the slope
    # note: k could be used as compressor gain
    s = 1 / (1 + np.exp(-x / k))
    return s


def generate_callback(qu: Queue, _gain: Queue):
    """
    _gain values are range(0, 100)
    """
    gain = 0.1
    try:
        while not _gain.empty():
            gain = _gain.get_nowait() / gain_divider
    except Empty:
        gain = 0.1

    def callback(indata, frames, time, status):
        nonlocal gain
        if status:
            text = " " + str(status) + " "
            print(text)
        try:
            while not _gain.empty():
                gain = _gain.get_nowait() / gain_divider
        except Empty:
            pass
        if any(indata):
            indata.shape = (frames,)
            qu.put_nowait((indata, gain))

    return callback


def calc_cqt(y, gain, sr=sr_44, harm=True):
    start = time.monotonic()
    if (
        abs(np.sum(y)) < gate_sum_threshold
        or max((abs(np.min(y)), abs(np.max(y)))) < gate_abs_threshold
    ):
        y = np.zeros(y.shape)
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

    if samples >= displaywindow:
        C = np.average(np.rot90(np.rot90(C)[:displaywindow], k=-1), axis=1)
    else:
        C = np.average(C, axis=1)
    # find maxima to clean some noise
    maxis = librosa.util.localmax(C)
    emphasis = (1.9, 0.9)  # how much we push maxima and pull neighbours
    mul = np.array(
        [emphasis[0] if maxis[_] else emphasis[1] for _ in range(len(maxis))]
    )
    C = mul * C

    # apply sigmoid
    C = C * (1 / np.max(C))
    C = norm(C)
    C = sigmoid(C, k=1 - gain)
    # normalize to 1
    P = norm(C, r=(0, 1))
    # format on palette width
    P = 9 * P  # palette width
    P = np.clip(P, 0, 9)  # TODO: should be no-op!
    P = P.astype(np.int8)
    P = P.reshape(6, 12)
    P = np.flip(P, axis=0)
    shape = io.StringIO()
    np.savetxt(shape, P, fmt="%s", delimiter="")
    shape = shape.getvalue()
    # print(time.monotonic() - start)
    return shape


def main(gain=0.1):
    qu = Queue(q_len)
    with sd.InputStream(
        device=device,
        channels=1,
        callback=generate_callback(qu, _gain=gain),
        blocksize=int(sr_44 * block_duration / 1000),
        samplerate=sr_44,
    ):
        data = np.empty((0, 0))
        while True:
            time.sleep(update_interval)
            p = None
            while not qu.empty():
                try:
                    p = qu.get()
                    indata, gain = p
                    data = np.append(data, indata)
                except Empty:
                    pass
            if len(data) > mindata:
                # discard some
                # print(len(data))
                shape = calc_cqt(data, gain)
                data = data[-window:]
                yield shape
