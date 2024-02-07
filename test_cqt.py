import scipy
import sounddevice
import librosa
import numpy as np
import matplotlib.pyplot as plt

sr_44 = 44100
sr_22 = 22500
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


def calc_cqt(y, sr=sr_44, harm=True):
    if harm:
        harm_y = librosa.effects.harmonic(y, margin=8)
    # print(y, y.shape)
    fmin = librosa.note_to_hz("C2")
    C = np.abs(
        librosa.cqt(
            y,
            sr=sr,
            fmin=fmin,
            bins_per_octave=12,
            n_bins=12 * 6,
        )
    )
    C_harm = np.abs(
        librosa.cqt(
            harm_y,
            sr=sr,
            fmin=fmin,
            bins_per_octave=12,
            n_bins=12 * 6,
        )
    )

    chroma_filter = np.minimum(
        C_harm,
        librosa.decompose.nn_filter(
            C_harm, aggregate=np.median, metric="cosine"
        ),
    )

    print("CQT" + ("harm" if harm is True else ""))
    fig, ax = plt.subplots(nrows=3, sharex=True, sharey=True)
    try:
        img1 = librosa.display.specshow(
            abs(C),
            sr=sr,
            x_axis="time",
            y_axis="cqt_note",
            ax=ax[0],
        )
        img2 = librosa.display.specshow(
            abs(C_harm),
            sr=sr,
            x_axis="time",
            y_axis="cqt_note",
            ax=ax[1],
        )
        img3 = librosa.display.specshow(
            abs(C_harm),
            sr=sr,
            x_axis="time",
            y_axis="cqt_note",
            ax=ax[2],
        )
        ax[0].set_title("Constant-Q power spectrum")
        ax[1].set_title("Harmonic Constant-Q power spectrum")
        fig.colorbar(img1, ax=ax, format="%+2.0f dB")
        fig.colorbar(img2, ax=ax, format="%+2.0f dB")
        fig.colorbar(img3, ax=ax, format="%+2.0f dB")
        plt.show()
    except Exception as ex:
        plt.close()
        raise ex


if __name__ == "__main__":
    frames = 100000
    # calc_cqt(librosa.load(librosa.ex("trumpet"))[0], sr=sr_22)
    import time

    while True:
        try:
            print(frames)
            time.sleep(1)
            y = get_data(frames)
            calc_cqt(y)
        except librosa.util.exceptions.ParameterError as ex:
            print(ex)
