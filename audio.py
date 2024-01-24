import pyaudio
from scipy import fft as FFT
import matplotlib.pyplot as plt
import numpy as np

pa = pyaudio.PyAudio()

DEVICE_NAME = "USB PnP Sound Device: Audio"
DEVICE_NAME = "jack"

RATE = 48000

def main():
    micid = None
    for _id in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(_id)
        print(f"{_id}: {dev['name']}")
        if dev["name"].startswith(DEVICE_NAME):
            micid = _id
            break

    print(f"device id is: {micid}")

    stream = pa.open(
        format=pyaudio.paInt16,
        rate=48000,
        channels=1,
        input_device_index=micid,
        input=True,
        frames_per_buffer=2**12,
    )
    print(stream)
    breakpoint()
    chunk = []

    if not stream.is_stopped():
        for _ in range(20):
            chunk = stream.read(2**12)
            print(len(chunk) > 0)
            y = np.fromstring(chunk, dtype=np.short)
            yy = np.array(y, dtype="d") / 32768.0
            inspectspec(yy)

    pa.close(stream)
    pa.terminate()



def inspectspec(data):
    """show fft plot data"""

    plt.figure(1)

    n = len(data)
    window = np.blackman(n)
    sumw = sum(window * window)

    A = FFT.fft(data * window)
    B2 = (A * np.conjugate(A)).real
    sumw *= 2.0
    sumw /= 1 / np.float64(RATE)  # sample rate
    B2 = B2 / sumw

    x = np.arange(0, n / 2, 1) / np.float64(n) * RATE

    eps = 1e-8
    plt.plot(x, np.log10(B2[0 : int(n / 2)] + eps))
    plt.show()

if __name__ == "__main__":
    main()
