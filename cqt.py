import time
import io
import sounddevice as sd
import librosa
import numpy as np
from queue import Empty, Queue

sr_44 = 44100
sr_22 = 22500
block_duration = 88
device = "USB"

FMIN = librosa.note_to_hz("C0")
GAIN = 5

def get_data():
    with sd.InputStream(
        device=device,
        samplerate=sr_44,
        blocksize=int(sr_44 * block_duration / 1000),
        callback=callback,
        channels=1,
    ) as stream:
        time.sleep(20)
        return 0


def generate_callback(qu: Queue, _gain=15):
    def callback(indata, frames, time, status):
        if status:
            print(status)
        print(frames)
        indata.shape = (frames,)
        qu.put_nowait(calc_cqt(indata))

    return callback


def calc_cqt(y, sr=sr_44, harm=True):
    start = time.monotonic()
    C = np.abs(
        librosa.cqt(
            y,
            sr=sr,
            fmin=FMIN,
            bins_per_octave=12,
            n_bins=12 * 6,
        )
    )
    C = np.average(C, axis=1)
    # P = C / np.linalg.norm(C)
    # P = P * (1 / np.max(P))
    gain = GAIN
    P = C * gain
    P = 9 * P  # palette width
    P = np.clip(P, 0, 9)
    I = P.astype(np.int8)
    I = I.reshape(6, 12)
    I = np.flip(I, axis=0)
    shape = io.StringIO()
    np.savetxt(shape, I, fmt="%s", delimiter="")
    shape = shape.getvalue()
    print(time.monotonic() - start)
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
        while True:
            p = None
            try:
                p = qu.get()
            except Empty:
                p = None
            if p is not None:
                yield p


if __name__ == "__main__":
    # calc_cqt(librosa.load(librosa.ex("trumpet"))[0], sr=sr_22)
    import time

    while True:
        try:
            start = time.monotonic()
            y = get_data()
            print("d", time.monotonic() - start)
            calc_cqt(y)

        except librosa.util.exceptions.ParameterError as ex:
            print(ex)
