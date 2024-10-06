from psychopy import prefs
prefs.hardware['audioLib'] = ['sounddevice']
prefs.hardware['audioDevice'] = 'Lautsprecher (RME Fireface UC)'  # Replace with your device name
prefs.hardware["audioLatencyMode"] = 3

from psychopy import sound, core

# Keep the window open for a short duration
core.wait(5)

# Create the sound stimulus
# setting speaker to 28 connects to default speakers of pc
sound_stimulus = sound.Sound(value='C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\stimuli\digits_all_250ms\\1.wav',
                             sampleRate=44100, stereo=True)
# Play the sound
sound_stimulus.play()
core.wait(2)
# core.quit()