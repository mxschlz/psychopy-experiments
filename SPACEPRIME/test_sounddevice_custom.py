from psychopy import parallel
import time
import os
os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd
import soundfile as sf


port = parallel.ParallelPort(0xCFF8)
sound_dir = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-102_block_0'
arrays = []
mul = 25
stream = sd.OutputStream(samplerate=44100, device=44, channels=3, latency=0.0, blocksize=0)

for sound_path in os.listdir(sound_dir):
    data, sr = sf.read(os.path.join(sound_dir, sound_path), dtype='float32')
    data = data * (10 ** (mul / 20))
    arrays.append(data)

sound = arrays[1]

stream.start()
for _ in range(30):
    stream.write(sound)
    port.setData(1)
    time.sleep(0.001)
    port.setData(0)
    time.sleep(0.5)


stream.stop()