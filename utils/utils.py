import os
from psychopy import sound


def load_stimuli(stimdir):
    """
    :param stimdir: stimulus directory
    :return: stimuli
    """
    # Load stimuli
    stimulus_pool = []
    stimnames = os.listdir(stimdir)
    for stimname in stimnames:
        print(f"Loading stimulus {stimname}")
        stim_fp = os.path.join(stimdir, stimname)
        stimulus_pool.append(sound.Sound(stim_fp))
    return stimulus_pool


if __name__ == '__main__':
    stimuli = load_stimuli('C:\\PycharmProjects\\psychopy-experiments\\stimuli\\digits_all_250ms')
