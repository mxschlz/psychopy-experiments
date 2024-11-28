import slab
import os
import matplotlib
import librosa
import numpy as np
matplotlib.use("TkAgg")

sounddir = "C:\\Users\AC_STIM\Documents\Experimentskripte\max_schulz_scripts\psychopy-experiments\SPACEPRIME\stimuli\\digits_all_250ms"
sounds = []
for filename in os.listdir(sounddir):
	sounds.append(slab.Sound.read(os.path.join(sounddir, filename)))

aligned_signals = []
onset_times = []

for sound in sounds:
	y = sound.data.flatten()
	sr = sound.samplerate
	# Detect the onset time
	onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
	onset_time = librosa.frames_to_time(onset_frames, sr=sr)[0]
	onset_times.append(onset_time)

# Find the earliest onset time
earliest_onset = min(onset_times)

# Align the signals by shifting them
for i, file in enumerate(sounds):
	y = file.data.flatten()
	sr = file.samplerate
	shift_samples = int((onset_times[i] - earliest_onset) * sr)
	print(shift_samples)
	aligned_signal = np.roll(y, -shift_samples).reshape(11025, 1)
	aligned_signals.append(aligned_signal)