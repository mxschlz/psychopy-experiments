from sound import Sound
from psychopy import core


soundfile = "C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\sequences\sub-99_block_0\s_0.wav"
device = 16

sound = Sound(filename=soundfile, device=device)

# test play sound
core.wait(5)
for _ in range(10):
	sound.play()
	core.wait(1)
