from psychopy import prefs
import sounddevice as sd
from psychtoolbox.audio import get_devices
from utils.sound import SoundDeviceSound
import os

prefs.hardware['audioLib'] = 'ptb'
prefs.hardware['audioDevice'] = 'Lautsprecher (Rubix24)'  # Replace with your device name
prefs.hardware["audioLatencyMode"] = 0
prefs.hardware["audioDriver"] = "Primary Sound"


from psychopy import sound
from psychopy import core

filename = "C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-101_block_0\\s_2.wav"
ptbs = sound.Sound(value=filename, stereo=False)
sds = SoundDeviceSound(filename, mul=1, device=44)
for i in range(20):
	core.wait(3)
	sds = SoundDeviceSound(filename, mul=1, device=3)
	sds.play()

print(sd.query_devices())
devices = get_devices()
print([x["DeviceName"] for x in devices if "Rubix" in x])

sounddir = "C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\stimuli\\targets_low_30_Hz"
sounds = [sound.Sound(value=os.path.join(sounddir, x)) for x in os.listdir(sounddir)]
#sounds = [WinSound(os.path.join(sounddir, x)) for x in os.listdir(sounddir)]

for x in os.listdir(sounddir):
	filepath = os.path.join(sounddir, x)
	sound1 = sound.Sound(value=filepath, speaker=0)
	sound2 = sound.Sound(value=filepath, speaker=1)
	sound3 = sound.Sound(value=filepath, speaker=2)
	sound1.play()
	sound2.play()
	sound3.play()
	core.wait(3)

for sound in sounds:
	core.wait(1)
	sound.play()
