from psychopy import visual, core, event, gui, data, parallel
import numpy as np
from encoding import FLANKER_MAP
import os.path as op
import os
import yaml
import collections
from psychopy import prefs as psychopy_prefs
from sound import SoundDeviceSound as Sound
import slab


# define trigger function
def send_trigger(trigger_name, port):
    # get corresponding trigger value:
    trigger_value = FLANKER_MAP[trigger_name]
    # send trigger to EEG:
    port.setData(trigger_value)
    core.wait(0.002)
    # turn off EEG trigger
    port.setData(0)

# function from SPACEPRIME to load settings file
def _load_settings(settings_file="config.yaml", output_dir="logs"):
    """Loads settings and sets preferences."""

    def _merge_settings(default, user):
        """Recursive dict merge. Inspired by dict.update(), instead of
        updating only top-level keys, dict_merge recurses down into dicts nested
        to an arbitrary depth, updating keys. The merge_dct is merged into
        Adapted from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9.

        Parameters
        ----------
        default : dict
            To-be-updated dict
        user : dict
            Dict to merge in default

        Returns
        -------
        None
        """
        for k, v in user.items():
            if (
                    k in default
                    and isinstance(default[k], dict)
                    and isinstance(user[k], collections.abc.Mapping)
            ):
                _merge_settings(default[k], user[k])
            else:
                default[k] = user[k]
    if not op.isfile(settings_file):
        raise IOError(f"Settings-file {settings_file} does not exist!")

    with open(settings_file, "r", encoding="utf8") as f_in:
        user_settings = yaml.safe_load(f_in)

    settings = user_settings

    # Write settings to sub dir
    if not op.isdir(output_dir):
        os.makedirs(output_dir)

    exp_prefs = settings["preferences"]  # set preferences globally
    for preftype, these_settings in exp_prefs.items():
        for key, value in these_settings.items():
            pref_subclass = getattr(psychopy_prefs, preftype)
            pref_subclass[key] = value
            setattr(psychopy_prefs, preftype, pref_subclass)
    return settings

# load up settings
settings = _load_settings()
# Get subject ID
subj_info = {"ID": "test",
             "test": True}
dlg = gui.DlgFromDict(subj_info, title="Flanker Task")
if not dlg.OK:
    core.quit()
# connect to parallel port
port = parallel.ParallelPort(0xCFF8)
# define params
params = {
    "n_reps": 36,
    "iti": 0.5,
    "stim_duration": 0.25,
    "location": [0, 1, 2],
    "sound_type": ["target", "distractor", "control"]
}
# Create a window
win = visual.Window(
    size=[1920, 1080],
    units="deg",
    fullscr=True,
    monitor="SPACEPRIME",
    color=[-1, -1, -1],  # Black background
)
# check if subject id is even or odd
if int(subj_info["ID"]) % 2 == 0:
    sub_id_is_even = True
elif int(subj_info["ID"]) % 2 != 0:
    sub_id_is_even = False

# get sound level
soundlvl = settings["session"]["level"]
# load up sounds with slab and adjust level
singletons = [slab.Sound.read(f"stimuli/distractors_{settings['session']['distractor_type']}/{x}")
              for x in os.listdir(f"stimuli/distractors_{settings['session']['distractor_type']}")]
targets_high = [slab.Sound.read(f"stimuli/targets_high_30_Hz/{x}") for x in
                os.listdir(f"stimuli/targets_high_30_hz")]
targets_low = [slab.Sound.read(f"stimuli/targets_low_30_Hz/{x}") for x in
               os.listdir(f"stimuli/targets_low_30_hz")]
others = [slab.Sound.read(f"stimuli/digits_all_250ms/{x}") for x in
          os.listdir(f"stimuli/digits_all_250ms")]

# set equal level --> this sets the RMS value of all sounds to an equal level :)
for s, th, tl, o in zip(singletons, targets_high, targets_low, others):
    s.level = soundlvl
    th.level = soundlvl
    tl.level = soundlvl
    o.level = soundlvl


if sub_id_is_even:
    # now, create to-be-used sound objects from slab data matrices
    targets = [Sound(data=x.data.flatten(),
                     device=settings["soundconfig"]["device"],
                     mul=settings["soundconfig"]["mul"],
                     sr = settings["session"]["samplerate"]) for x in targets_low]
    distractors = [Sound(data=x.data.flatten(),
                         device=settings["soundconfig"]["device"],
                         mul=settings["soundconfig"]["mul"],
                         sr = settings["session"]["samplerate"]) for x in singletons]
    controls = [Sound(data=x.data.flatten(),
                      device=settings["soundconfig"]["device"],
                      mul=settings["soundconfig"]["mul"],
                      sr = settings["session"]["samplerate"]) for x in others]
elif not sub_id_is_even:
    targets = [Sound(data=x.data.flatten(),
                     device=settings["soundconfig"]["device"],
                     mul=settings["soundconfig"]["mul"],
                     sr = settings["session"]["samplerate"]) for x in targets_high]
    distractors = [Sound(data=x.data.flatten(),
                         device=settings["soundconfig"]["device"],
                         mul=settings["soundconfig"]["mul"],
                         sr = settings["session"]["samplerate"]) for x in others]
    controls = [Sound(data=x.data.flatten(),
                      device=settings["soundconfig"]["device"],
                      mul=settings["soundconfig"]["mul"],
                      sr = settings["session"]["samplerate"]) for x in singletons]
