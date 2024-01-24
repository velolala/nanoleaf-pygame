import pyaudio

pa = pyaudio.PyAudio()

for _id in range(pa.get_device_count()):
    if pa.get_device_info_by_index(_id)["name"].startswith(
        "USB PnP Sound Device: Audio"
    ):
        micid = _id
        break

stream = pa.open(
    format=pyaudio.paInt16,
    rate=44100,
    channels=1,
    input_device_index=micid,
    input=True,
    frames_per_buffer=2**12,
)
chunk = []

while not stream.is_stopped():
    chunk = stream.read(2**12)
