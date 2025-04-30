from SPACEPRIME.utils.signal_processing import *
import os
import slab
import yaml

# load settings
settings_path = "config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)

# stimulus root
root = settings["filepaths"]["stimuli"]
stimdir = os.path.join(root, "digits_all_250ms")

# load up stimuli and further save them level ajdusted
orig_stims = []
for i in os.listdir(stimdir):
    sound_path = os.path.join(stimdir, i)
    orig_stim = slab.Sound.read(sound_path)
    orig_stims.append(orig_stim)
    orig_stim.level = 50
    orig_stim.write(sound_path, normalise=False)

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
    high_pitched_distractor.level = 50
    high_pitched_distractor.write(os.path.join(distractor_high_dir, digit + f"_high_pitched_factor_{high_pitch_factor}.wav"),
                                  normalise=False)

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
    target_low.level = 50
    target_low.write(os.path.join(targetdir_low, digit + f"_amplitude_modulated_{modulation_freq}.wav"),
                     normalise=False)
    target_high = shift_pitch(stim, pitch_factor=high_pitch_factor)
    target_high = modulate_amplitude(target_high, modulation_freq=modulation_freq)
    target_high.level = 50
    target_high.write(os.path.join(targetdir_high, digit + f"_amplitude_modulated_{modulation_freq}.wav"),
                      normalise=False)

