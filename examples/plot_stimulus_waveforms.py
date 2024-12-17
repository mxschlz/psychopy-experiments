import matplotlib
matplotlib.use("Qt5Agg")
import os
import slab
import matplotlib.pyplot as plt
plt.ion()


sounddir = "C:\\Users\Max\PycharmProjects\psychopy-experiments\SPACEPRIME\stimuli\\digits_all_250ms"
sounds = []
for filename in os.listdir(sounddir):
	sound = slab.Sound.read(os.path.join(sounddir, filename))
	sound.waveform(show=False)
	plt.savefig(f"G:\Meine Ablage\PhD\misc\\stim_{filename}.svg")
	plt.close()