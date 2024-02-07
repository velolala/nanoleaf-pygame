import scipy
import sounddevice
import librosa
import numpy as np
import matplotlib.pyplot as plt

sr_44 = 44100
sr_22 = 22500
sr_22 = sr_44
block_duration = 22


def get_data(num=1):
    with sounddevice.InputStream(
        device="USB",
        samplerate=sr_44,
        blocksize=int(sr_44 * block_duration / 1000),
        channels=1,
    ) as stream:
        data = stream.read(num)
        y = data[0]
        y.shape = (len(data[0]),)
        return y


def calc_cqt(y):
    print(y, y.shape)
    C = np.abs(
        librosa.cqt(
            y,
            sr=sr_22,
            fmin=librosa.note_to_hz("C4"),
            bins_per_octave=12,
            n_bins=12,
        )
    )
    print("CQT")
    fig, ax = plt.subplots()
    try:
        img = librosa.display.specshow(
            abs(C),
            sr=sr_22,
            x_axis="time",
            y_axis="cqt_note",
            ax=ax,
        )
        ax.set_title("Constant-Q power spectrum")
        fig.colorbar(img, ax=ax, format="%+2.0f dB")
        plt.show()
    except Exception as ex:
        plt.close()
        raise ex


if __name__ == "__main__":
    frames = 200
    calc_cqt(librosa.load(librosa.ex("trumpet"))[0])
    while True:
        try:
            print(frames)
            y = get_data(frames)
            calc_cqt(y)
        except librosa.util.exceptions.ParameterError as ex:
            print(ex)
        frames *= 2
