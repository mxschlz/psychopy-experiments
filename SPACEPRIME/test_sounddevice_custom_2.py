from psychopy import parallel
import time
import os
os.environ["SD_ENABLE_ASIO"] = "1"
import soundfile as sf
from obsolete.custom_sound import SoundSD


port = parallel.ParallelPort(0xCFF8)
sound_dir = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-102_block_0'
data, sr = sf.read(
    'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-102_block_0\s_1.wav')
mul = 25
data = data * (10 ** (mul / 20))
sound = SoundSD(data=data, device=44, sample_rate=sr)
arrays = []


for _ in range(30):
    sound.play(when=0.1)
    #time.sleep(0.5)  # to be replace with an higher precision sleep function
    port.setData(1)
    time.sleep(0.001)
    port.setData(0)
    time.sleep(1.0)
