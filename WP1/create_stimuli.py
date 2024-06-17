from utils.signal_processing import *
import os
import slab
import yaml

# stimulus root
root = "C:\\PycharmProjects\\psychopy-experiments\\stimuli\\"
stimdir = os.path.join(root, "digits_all_250ms")

# load settings
settings_path = "WP1/config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)


# load up stimuli
orig_stims = [slab.Sound.read(os.path.join(stimdir, f"{i}")) for i in os.listdir(stimdir)]


# make distractors of low and high saliency
distractor_low_dir = os.path.join(root, "distractors_low")
distractor_high_dir = os.path.join(root, "distractors_high")
try:
    os.mkdir(distractor_high_dir)
    os.mkdir(distractor_high_dir)
except FileExistsError:
    print(f"Directory {distractor_low_dir} or {distractor_high_dir} already exists")

# for distractor generation, we need to change the pitch. we do this by increasing and decreasing the pitch of the
# original stimuli.
low_pitch_factor = -10
high_pitch_factor = 10
for stimname, stim in zip(os.listdir(stimdir), orig_stims):
    digit = stimname.split(".")[0]
    low_pitched = shift_pitch(stim, pitch_factor=low_pitch_factor)  # low pitched
    low_pitched.write(os.path.join(distractor_low_dir, digit + f"_low_pitched_factor_{low_pitch_factor}.wav"))
    high_pitched = shift_pitch(stim, pitch_factor=high_pitch_factor)  # high pitched
    high_pitched.write(os.path.join(distractor_high_dir, digit + f"_high_pitched_factor_{high_pitch_factor}.wav"))

# make targets
modulation_freq = 30  # amplitude modulation

# generate target directory
targetdir = os.path.join(root, f"targets_{modulation_freq}_Hz")
try:
    os.mkdir(targetdir)
except FileExistsError:
    print(f"Directory {targetdir} already exists")

for stimname, stim in zip(os.listdir(stimdir), orig_stims):
    digit = stimname.split(".")[0]
    target = modulate_amplitude(stim, modulation_freq=modulation_freq)  # low pitched
    target.write(os.path.join(targetdir, digit + f"_amplitude_modulated_{modulation_freq}.wav"))

