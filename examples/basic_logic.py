from psychopy import sound, visual, core, event, data, gui
import random
import yaml
import os
import sys
import WP1.prompts as instruction
from utils import utils, set_logging_level
from exptools2.core import Session


# Set up the window
window = visual.Window(size=windowparams['window_size'], fullscr=windowparams['fullscreen'],
                       screen=windowparams["screen"], allowGUI=textparams["allowgui"], color=windowparams['bg_color'],
                       colorSpace=windowparams["colorspace"])

instructions = visual.TextStim(window, color=textparams["color"], text=instruction.welcome, units=textparams["units"],
                               height=textparams["height"], font=textparams["font"])

# Display the instructions and wait for the space bar to be hit to start
instructions.draw()
window.flip()
event.waitKeys(keyList=['space'])

# initialise some stimuli
fixation = visual.TextStim(window, "+")
fixation.draw(window)

# Load stimuli
stimulus_pool = utils.load_stimuli(stimparams["fp"])

# Setup trial handler
trials = data.TrialHandler(nReps=stimparams['n_reps'], method=stimparams["method"], trialList=stimparams['trial_list'])

# Create a dictionary to store results
# TODO: what to save?
results = {'trial': [], 'targetpos': [], 'singleton_present': [], 'response': [], 'rt': [], "correct": [],
           "singletonpos": []}

# TODO: pseudorandomize trials
# Run experiment
for trial in trials:
    target_location = random.randint(1, 5)
    singleton_present = random.random() < 0.5

    # Set up stimuli for this trial
    trial_sounds = []
    for i in range(5):
        if i == target_location - 1:
            trial_sounds.append(stimulus_pool[4])  # '5' digit
        else:
            trial_sounds.append(random.choice(stimulus_pool[:4]))  # Random digit other than '5'

    if singleton_present:
        singleton_location = random.choice([loc for loc in range(5) if loc != target_location - 1])
        # TODO: generate singleton distractor .wav files
        trial_sounds[singleton_location] = sound.Sound('stimuli/audio_files/singleton_distractor.wav')

    # Play sounds
    # TODO: play sounds simultaneously instead of serially
    for idx, snd in enumerate(trial_sounds):
        snd.play()
        core.wait(stimparams['stimulus_duration'])

    # Collect response
    clock = core.Clock()
    response = event.waitKeys(keyList=['1', '2', '3', '4', '5'], timeStamped=clock)

    if response:
        key, rt = response[0]
    else:
        key, rt = None, None

    # Store data
    results['trial'].append(trials.thisN)
    results['target_location'].append(target_location)
    results['singleton_present'].append(singleton_present)
    results['response'].append(key)
    results['rt'].append(rt)

    # Inter-trial interval
    core.wait(config['iti'])

# Save results
data_file = os.path.join('data/raw', f'results_{data.getDateStr()}.csv')
data.saveAsWideText(data_file, stimOut=None, dataOut=['all_raw'])

# Clean up
window.close()
core.quit()