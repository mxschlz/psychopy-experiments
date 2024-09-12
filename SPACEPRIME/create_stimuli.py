from utils.signal_processing import *
import os
import slab
import yaml

# stimulus root
root = "C:\\PycharmProjects\\psychopy-experiments\\stimuli\\"
stimdir = os.path.join(root, "digits_all_250ms")

# load settings
settings_path = "SPACEPRIME/config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)


# load up stimuli
orig_stims = [slab.Sound.read(os.path.join(stimdir, f"{i}")) for i in os.listdir(stimdir)]

# make distractors of low and high saliency
distractor_high_dir = os.path.join(root, "distractors_high")

try:
    os.mkdir(distractor_high_dir)
except FileExistsError:
    print(f"stimuli directories exist already!")

# for distractor generation, we need to change the pitch. we do this by increasing and decreasing the pitch of the
# original stimuli.
high_pitch_factor = 10
for stimname, stim in zip(os.listdir(stimdir), orig_stims):
    digit = stimname.split(".")[0]
    high_pitched_distractor = shift_pitch(stim, pitch_factor=high_pitch_factor)  # high pitched
    high_pitched_distractor.write(os.path.join(distractor_high_dir, digit + f"_high_pitched_factor_{high_pitch_factor}.wav"))

# make targets
modulation_freq = 30  # amplitude modulation

# generate target directory
targetdir_high = os.path.join(root, f"targets_high_{modulation_freq}_Hz")
targetdir_low = os.path.join(root, f"targets_low_{modulation_freq}_Hz")
try:
    os.mkdir(targetdir_high)
    os.mkdir(targetdir_low)
except FileExistsError:
    print(f"Directory already exists")

for stimname, stim in zip(os.listdir(stimdir), orig_stims):
    digit = stimname.split(".")[0]
    target_low = modulate_amplitude(stim, modulation_freq=modulation_freq)  # low pitched
    target_low.write(os.path.join(targetdir_low, digit + f"_amplitude_modulated_{modulation_freq}.wav"))
    target_high = shift_pitch(stim, pitch_factor=high_pitch_factor)
    target_high = modulate_amplitude(target_high, modulation_freq=modulation_freq)
    target_high.write(os.path.join(targetdir_high, digit + f"_amplitude_modulated_{modulation_freq}.wav"))
