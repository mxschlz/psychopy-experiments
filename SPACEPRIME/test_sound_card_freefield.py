from psychopy import prefs
import sounddevice as sd
import soundfile as sf
import numpy as np
from psychtoolbox.audio import get_devices
prefs.hardware['audioLib'] = 'sounddevice'
prefs.hardware['audioDevice'] = 'Analog (5+6) (RME Fireface UC)'  # Replace with your device name
prefs.hardware["audioLatencyMode"] = 3

from psychopy import sound, core

print(sd.query_devices())
devices = get_devices()
sp = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\stimuli\digits_all_250ms\\1.wav'
data, fs = sf.read(sp)
ext_dim = np.tile(data, (3, 1)).transpose()

# Create the sound stimulus
# setting speaker to 28 connects to default speakers of pc
stim = sound.Sound(value=sp, sampleRate=fs)
# Play the sound
stim.play()


# play via soundcard module
sd.play(data, fs, device=16)

sp1 = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\stimuli\digits_all_250ms\\1.wav'
sp2 = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\stimuli\digits_all_250ms\\5.wav'
sp3 = 'C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\stimuli\digits_all_250ms\\9.wav'

combined = np.array([sf.read(sp1)[0], sf.read(sp2)[0], sf.read(sp3)[0]]).transpose()

core.wait(5)
sd.play(combined, fs, device=11)


# go through all devices and try to play a sound
core.wait(5)
for i in range(len(sd.query_devices())):
	print(i)
	try:
		sd.play(data, fs, device=i)
	except:
		continue
	core.wait(1)


# middle loudspeaker indices
core.wait(5)
for e in [16,36,47,73]:
	print(e)
	sd.play(data, fs, device=e)
	core.wait(0.5)


# headphone indices
core.wait(5)
for e in [16, 38, 48, 77]:
	print(e)
	sd.play(data, fs, device=e)
	core.wait(1)
