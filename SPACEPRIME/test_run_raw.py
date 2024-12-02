from psychopy import parallel
import os
os.environ["SD_ENABLE_ASIO"] = "1"
from SPACEPRIME.sound import SoundDeviceSound
import time


port = parallel.ParallelPort(0xCFF8)
sound_dir = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-102_block_0'
sounds = []
for x in os.listdir(sound_dir):
    sounds.append(SoundDeviceSound(os.path.join(sound_dir, x), device=44, mul=25))

for i, _ in enumerate(range(30)):
    print(f"Playing sound {i}")
    sounds[i].play(latency=0.0, blocksize=0)
    time.sleep(0.08)
    port.setData(1)
    time.sleep(0.001)
    port.setData(0)
    time.sleep(0.5)
