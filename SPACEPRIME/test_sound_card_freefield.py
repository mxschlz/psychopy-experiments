import slab
import os
from psychopy import prefs, sound

# Get a list of available audio devices
devices = sound.getDevices()
device_name = 'Lautsprecher (RME Fireface UC)'

# Find the index of the desired device
device_index = devices[device_name]["DeviceIndex"]
# If the device was found, set it as the preferred output device
if device_index is not None:
    prefs.hardware['audioLib'] = ['ptb']  # Ensure sounddevice is used
    prefs.hardware['audioDevice'] = device_name
    print(f"Audio device set to: {devices[device_name]}")
else:
    print("Desired audio device not found.")




sound_dir = "C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-99_block_0"

sounds = [slab.Sound.read(os.path.join(sound_dir, x)) for x in os.listdir(sound_dir)]
sound_path = os.path.join(sound_dir, os.listdir(sound_dir)[0])

stim = sound.Sound(sound_path)
