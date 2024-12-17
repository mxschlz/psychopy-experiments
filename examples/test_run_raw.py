from psychopy import parallel
import os
os.environ["SD_ENABLE_ASIO"] = "1"
# from SPACEPRIME.sound import SoundDeviceSound
import sounddevice as sd
import soundfile as sf
import time


port = parallel.ParallelPort(0xCFF8)
mul = 20
sound_dir = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-102_block_0'
sounds = []
stream = sd.OutputStream(samplerate=44100, blocksize=0, device=44, channels=3, latency=0.0, dtype="float32")
stream.start()
for x in os.listdir(sound_dir):
    data = sf.read(os.path.join(sound_dir, x), dtype="float32")[0]
    data_louder = data * (10 ** (mul / 20))
    sounds.append(data_louder)

for i, _ in enumerate(range(30)):
    print(f"Playing sound {i}")
    port.setData(1)
    time.sleep(0.003)
    port.setData(0)
    stream.write(sounds[i])
    time.sleep(0.5)
