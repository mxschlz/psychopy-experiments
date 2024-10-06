from psychopy import prefs
prefs.hardware['audioLib'] = ['ptb']
prefs.hardware['audioDevice'] = 'Lautsprecher (RME Fireface UC)'  # Replace with your device name

from psychopy import sound

print(sound.Sound)