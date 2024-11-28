from psychopy import parallel
from SPACEPRIME.sound import SoundDeviceSound
import time
import os


port = parallel.ParallelPort(0xCFF8)
sound_dir = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-102_block_0'
sounds = []
for sound_path in os.listdir(sound_dir):
    sound = SoundDeviceSound(os.path.join(sound_dir, sound_path), device=44, mul=25)
    sounds.append(sound)

for i in range(15):
    sounds[i].play()
    time.sleep(0.08)
    port.setData(1)
    time.sleep(0.001)
    port.setData(0)
    time.sleep(1)
