from psychopy import visual, core, event, gui, data, parallel
import numpy as np
from encoding import FLANKER_MAP
from psychopy.event import waitKeys
from datetime import datetime


# define trigger function
def send_trigger(trigger_name, port):
    # get corresponding trigger value:
    trigger_value = FLANKER_MAP[trigger_name]
    # send trigger to EEG:
    port.setData(trigger_value)
    core.wait(0.002)
    # turn off EEG trigger
    port.setData(0)
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
    "n_reps": 40,
    "iti": 0.5,
    "stim_duration": 0.05
}
# Create a window
win = visual.Window(
    size=[1920, 1080],
    units="deg",
    fullscr=True,
    monitor="SPACEPRIME",
    color=[-1, -1, -1],  # Black background
)
# Define stimuli
target = visual.TextStim(
    win=win,
    text="",
    height=2,
    color="#FFFFFF",  # White text
    pos=[0, 0],
)
flanker_left = visual.TextStim(
    win=win,
    text="",
    height=2,
    color="#FFFFFF",  # White text
    pos=[-2, 0],  # Positioned to the left of the target
)
flanker_right = visual.TextStim(
    win=win,
    text="",
    height=2,
    color="#FFFFFF",  # White text
    pos=[2, 0],  # Positioned to the right of the target
)
# Define trial types
trial_types = [
    {"target": "<", "flankers": "<<", "congruency": "congruent", "correct_response": "left"},
    {"target": ">", "flankers": ">>", "congruency": "congruent", "correct_response": "right"},
    {"target": "<", "flankers": ">>", "congruency": "incongruent", "correct_response": "left"},
    {"target": ">", "flankers": "<<", "congruency": "incongruent", "correct_response": "right"},
    {"target": ">", "flankers": "□□", "congruency": "neutral", "correct_response": "right"},
    {"target": "<", "flankers": "□□", "congruency": "neutral", "correct_response": "left"}
]
if subj_info["test"]:
    # Create trial handler
    trials = data.TrialHandler(
        trial_types,
        nReps=2,  # Number of repetitions for each trial type
        method="random",
    )
elif not subj_info["test"]:
    # Create trial handler
    trials = data.TrialHandler(
        trial_types,
        nReps=params["n_reps"],  # Number of repetitions for each trial type
        method="random",
    )
# Create a file to save data
filename = f"logs/flanker_data_{subj_info['ID']}_{datetime.now().strftime('%B_%d_%Y_%H_%M_%S')}.csv"
if not subj_info["test"]:
    data_file = open(filename, "w")
    data_file.write("subject_id,trial_number,target,congruency,response,rt,correct\n")
# write instructions
instruction_text = """
In dieser Aufgabe werden Ihnen Pfeile angezeigt, die nach links oder rechts zeigen.\n
Ihre Aufgabe ist es, so schnell und genau wie möglich die Richtung des mittleren Pfeils zu bestimmen.\n
Drücken Sie dafür die entsprechende Taste (z.B. linke Taste für links, rechte Taste für rechts).\n
Es ist wichtig, dass Sie sich nur auf den mittleren Pfeil konzentrieren und die Pfeile, die ihn umgeben, ignorieren.\n

Drücken Sie LEERTASTE, um zu beginnen.
"""
# display instructions
instructions = visual.TextStim(win, text=instruction_text, height=0.75)
instructions.draw()
win.flip()
# wait for space press to continue
waitKeys(keyList="space")
# Start the clock
trial_clock = core.Clock()
# wait for 1 second before displaying stimuli
for wait_time in reversed(range(1, 4)):
    waiting = visual.TextStim(win, f"Starting experiment in {wait_time} seconds ... ", height=0.75)
    waiting.draw()
    win.flip()
    core.wait(1)
# Run the experiment
trial_count = 0
for trial in trials:
    # make mouse invisible
    win.setMouseVisible(False)
    if trial["correct_response"] == "left" and trial["congruency"] == "congruent":
        trigger_name = "congruent_left"
    elif trial["correct_response"] == "left" and trial["congruency"] == "incongruent":
        trigger_name = "incongruent_left"
    elif trial["correct_response"] == "right" and trial["congruency"] == "congruent":
        trigger_name = "congruent_right"
    elif trial["correct_response"] == "right" and trial["congruency"] == "incongruent":
        trigger_name = "incongruent_right"
    elif trial["correct_response"] == "left" and trial["congruency"] == "neutral":
        trigger_name = "neutral_left"
    elif trial["correct_response"] == "right" and trial["congruency"] == "neutral":
        trigger_name = "neutral_right"
    else:
        trigger_name = "none"
    trial_count += 1
    # Set the stimuli for the current trial
    target.text = trial["target"]
    flanker_left.text = trial["flankers"]
    flanker_right.text = trial["flankers"]
    # Display the stimuli
    target.draw()
    flanker_left.draw()
    flanker_right.draw()
    win.callOnFlip(send_trigger,trigger_name, port)
    win.flip()
    # wait for stim duration
    core.wait(params["stim_duration"])
    # Clear the screen
    win.flip()
    trial_clock.reset()
    # Wait for a response
    keys = event.waitKeys(keyList=["left", "right"], maxWait=1.2)
    # Record response and reaction time
    response = keys[0] if keys else 0
    # Check if 'q' key is pressed
    if 'q' in event.getKeys():
        # Stop the experiment
        core.quit()
    rt = trial_clock.getTime()  # Get reaction time from the clock
    # Check if the response is correct
    correct = response == trial["correct_response"]
    # Write data to file
    if not subj_info["test"]:
        data_file.write(
            f"{subj_info['ID']},{trial_count},{trial['target']},{trial['congruency']},{response},{rt},{correct}\n"
        )
    # Inter-trial interval
    core.wait(np.random.uniform(params["iti"]-params["iti"]*0.25, params["iti"]+params["iti"]*0.25))

if not subj_info["test"]:
    # Close the data file
    data_file.close()
# Close the window
win.close()