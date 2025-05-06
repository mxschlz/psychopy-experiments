from psychopy import visual, core, event, gui, parallel
import os
os.environ["SD_ENABLE_ASIO"] = "1"
import numpy as np
from encoding import PASSIVE_LISTENING_MAP
import os.path as op
import yaml
import collections
from psychopy import prefs as psychopy_prefs
from utils.sound import SoundDeviceSound as Sound
from itertools import product


# define trigger function
def send_trigger(trigger_name, port):
    # get corresponding trigger value:
    trigger_value = PASSIVE_LISTENING_MAP[trigger_name]
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
subj_info = {"ID": 999}
dlg = gui.DlgFromDict(subj_info, title="Passive Listening")
if not dlg.OK:
    core.quit()
# connect to parallel port
port = parallel.ParallelPort(0xCFF8)
# define params
params = {
    "n_reps": 4,
    "n_digits": 9,
    "iti": 0.6,
    "stim_duration": 0.25,
    "locations": [1, 2, 3],
    "sound_types": ["target", "distractor", "control"]
}
# Create a window
win = visual.Window(
    size=[1920, 1080],
    units="deg",
    fullscr=True,
    monitor="SPACEPRIME",
    color=[0, 0, 0]  # grey background
)
# check if subject id is even or odd
if int(subj_info["ID"]) % 2 == 0:
    sub_id_is_even = True
elif int(subj_info["ID"]) % 2 != 0:
    sub_id_is_even = False


# define stimuli types based on subject ID
if sub_id_is_even:
    # now, create to-be-used sound objects from slab data matrices
    targets = [Sound(filename=os.path.join(f"stimuli\\targets_low_30_Hz", x),
                     device=settings["soundconfig"]["device"],
                     mul=settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\targets_low_30_Hz")]
    distractors = [Sound(filename=os.path.join(f"stimuli\\distractors_high", x),
                         device=settings["soundconfig"]["device"],
                         mul=settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\distractors_high")]
    controls = [Sound(filename=os.path.join(f"stimuli\\digits_all_250ms", x),
                      device=settings["soundconfig"]["device"],
                      mul=settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\digits_all_250ms")]
elif not sub_id_is_even:
    targets = [Sound(filename=os.path.join(f"stimuli\\targets_high_30_Hz", x),
                     device=settings["soundconfig"]["device"],
                     mul=settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\targets_high_30_Hz")]
    distractors = [Sound(filename=os.path.join(f"stimuli\\digits_all_250ms", x),
                         device=settings["soundconfig"]["device"],
                         mul=settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\digits_all_250ms")]
    controls = [Sound(filename=os.path.join(f"stimuli\\distractors_high", x),
                      device=settings["soundconfig"]["device"],
                      mul=settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\distractors_high")]

fixation_cross = visual.TextStim(
    win=win,
    text="+",
    color="#FFFFFF",  # White text
    pos=[0, 0],  # Positioned to the right of the target
)


def create_pseudorandom_sequence(locations, sound_types, n_reps, n_digits):
  """
  Creates a pseudorandomized trial sequence with no immediate repetition
  of number, location, OR sound type.

  Args:
    locations: List of spatial locations.
    sound_types: List of sound types.
    n_reps: Number of repetitions for each condition.

  Returns:
    A numpy array with the trial sequence.
  """
  all_trials = list(product(locations, sound_types, range(1, n_digits+1))) * n_reps
  np.random.shuffle(all_trials)

  trialsequence = []
  prev_location = None
  prev_number = None
  prev_sound_type = None  # Add this line

  def _backtrack(idx):
    nonlocal prev_location, prev_number, prev_sound_type  # Add prev_sound_type
    if idx == len(all_trials):
      return True

    for i in range(idx, len(all_trials)):
      location, sound_type, number = all_trials[i]
      # Check for repetition of location, number, OR sound_type
      if (location == prev_location or
          number == prev_number or
          sound_type == prev_sound_type):  # Add this condition
        continue

      trialsequence.append(all_trials[i])
      prev_location = location
      prev_number = number
      prev_sound_type = sound_type  # Update prev_sound_type
      all_trials[i], all_trials[idx] = all_trials[idx], all_trials[i]

      if _backtrack(idx + 1):
        return True

      # Backtrack
      trialsequence.pop()
      prev_location = trialsequence[-1][0] if trialsequence else None
      prev_number = trialsequence[-1][2] if trialsequence else None
      prev_sound_type = trialsequence[-1][1] if trialsequence else None  # Update
      all_trials[i], all_trials[idx] = all_trials[idx], all_trials[i]

    return False

  _backtrack(0)
  return np.array(trialsequence)


trialsequence = create_pseudorandom_sequence(
    params["locations"], params["sound_types"], params["n_reps"], params["n_digits"]  # Adjust n_reps
)
# Write the numpy array directly to a CSV file
np.savetxt(f'sequences\sub-{int(subj_info["ID"])}_passive_listening_sequence.csv', trialsequence, delimiter=',',
           fmt='%s',
           header='location,sound_type,digit', comments='')
# write instructions
instruction_text = """
In den kommenden 5 Minuten werden Ihnen Geräusche aus verschiedenen Lautsprechern in schneller Abfolge präsentiert.\n
Sie müssen nichts weiter tun, als auf das Fixationskreuz vor Ihnen zu schauen.\n
Danach geht es mit der Hauptaufgabe weiter.\n


Drücken Sie LEERTASTE, um zu beginnen.
"""
# display instructions
instructions = visual.TextStim(win, text=instruction_text, height=0.75)
instructions.draw()
win.flip()
# wait for space press to continue
event.waitKeys(keyList="space")
# wait for 1 second before displaying stimuli
for wait_time in reversed(range(1, 4)):
    waiting = visual.TextStim(win, f"Starting experiment in {wait_time} seconds ... ", height=0.75)
    waiting.draw()
    win.flip()
    core.wait(1)
# display fixation cross
fixation_cross.draw()
win.flip()
# iterate over trialsequence
for trial in trialsequence:
    # make mouse invisible
    win.setMouseVisible(False)
    if trial[1] == "distractor":
        stim = distractors[int(trial[2])-1]
    elif trial[1] == "target":
        stim = targets[int(trial[2])-1]
    elif trial[1] == "control":
        stim = controls[int(trial[2])-1]
    trigger_name = f"{trial[1]}-location-{trial[0]}-number-{trial[2]}"
    stim.play(latency="low", mapping=int(trial[0]), blocksize=0)
    #stim.play(latency="low", mapping=3, blocksize=0)
    core.wait(0.08)  # fucking 80 ms wait LOL
    send_trigger(trigger_name=trigger_name, port=port)
    #send_trigger(trigger_name="test_trigger", port=port)
    core.wait(params["stim_duration"])
    #core.wait(0.08)
    if 'q' in event.getKeys():
        # Stop the experiment
        core.quit()
    # Inter-trial interval
    core.wait(np.random.uniform(params["iti"]-0.2, params["iti"]+0.2))

# Close the window
win.close()