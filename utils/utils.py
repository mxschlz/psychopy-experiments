import os
from psychopy import sound, gui, __version__
import pandas as pd
import numpy as np


def get_input_from_dict(input_dict, title="Input Values"):
    """
    Presents a dialog box to collect input values based on a dictionary.

    Args:
        input_dict: A dictionary where keys are labels and values are initial values or choices.
        title: The title of the dialog box.

    Returns:
        A dictionary containing the collected input values.
    """
    input_dict["PsychoPy Version"] = __version__
    dlg = gui.DlgFromDict(dictionary=input_dict, title=title, fixed=["PsychoPy Version"])

    if dlg.OK:
        if input_dict["subject_id"]:
            if input_dict["subject_id"] < 10:
                input_dict["subject_id"] = f'0{input_dict["subject_id"]}'
        return input_dict  # Input values have been updated in the original dictionary
    else:
        return None  # User canceled the dialog


def load_stimuli(stimdir):
    """Loads sound stimuli from a directory.

    This function iterates through the specified directory, loads each sound file
    it finds, and returns them as a list of `slab.Sound` objects.

    Args:
      stimdir: The path to the directory containing the sound files.

    Returns:
      A list of `slab.Sound` objects representing the loaded stimuli.

    Raises:
      FileNotFoundError: If the specified directory does not exist.

    Example:
      ```
      stimuli = load_stimuli('./sounds')  # Load stimuli from './sounds' directory
      ```
    """

    stimulus_pool = []
    stimnames = os.listdir(stimdir)
    for stimname in stimnames:
        print(f"Loading stimulus {stimname}")
        stim_fp = os.path.join(stimdir, stimname)
        stimulus_pool.append(sound.Sound(stim_fp))
    return stimulus_pool


def generate_balanced_jitter(df, iti, tolerance=0.001):
    df_0 = df[df['SingletonPresent'] == 0]
    df_1 = df[df['SingletonPresent'] == 1]

    while True:
        jitter_0 = np.random.uniform(iti-iti*0.25, iti+iti*0.25, size=len(df_0))
        jitter_1 = np.random.uniform(iti-iti*0.25, iti+iti*0.25, size=len(df_1))

        mean_jitter_0 = np.mean(jitter_0)
        mean_jitter_1 = np.mean(jitter_1)

        if abs(mean_jitter_0 - mean_jitter_1) < tolerance:
            break

    return pd.Series(np.concatenate([jitter_0, jitter_1]), index=df.index)


if __name__ == '__main__':
    info = get_input_from_dict(input_dict={"participant_info": 99})
    # stimuli = load_stimuli('C:\\PycharmProjects\\psychopy-experiments\\stimuli\\digits_all_250ms')
