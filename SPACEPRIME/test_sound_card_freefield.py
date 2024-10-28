from psychopy import prefs
import sounddevice as sd
from psychtoolbox.audio import get_devices
import os


prefs.hardware['audioLib'] = 'sounddevice'
prefs.hardware['audioDevice'] = 'ASIO Fireface USB'  # Replace with your device name
prefs.hardware["audioLatencyMode"] = 3
prefs.hardware["audioDriver"] = "ASIO"

from SPACEPRIME.sound import WinSound
#from psychopy import sound
from psychopy import core

print(sd.query_devices())
devices = get_devices()
print([x["DeviceName"] for x in devices if "ASIO" in x])

sounddir = "C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\stimuli\\targets_low_30_Hz"
#sounds = [Sound(filename=os.path.join(sounddir, x), device=44, mul=1) for x in os.listdir(sounddir)]
sounds = [WinSound(os.path.join(sounddir, x)) for x in os.listdir(sounddir)]

for sound in sounds:
	core.wait(1)
	sound.play()
