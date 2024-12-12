from psychopy import visual, core, event, gui, data

# Get subject ID
subj_info = {"ID": ""}
dlg = gui.DlgFromDict(subj_info, title="Flanker Task")
if not dlg.OK:
    core.quit()

# Create a window
win = visual.Window(
    size=[800, 600],
    units="deg",
    fullscr=False,
    monitor="testMonitor",
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
    {"target": ">", "flankers": "oo", "congruency": "na", "correct_response": "right"},
    {"target": "<", "flankers": "oo", "congruency": "na", "correct_response": "left"}
]

# Create trial handler
trials = data.TrialHandler(
    trial_types,
    nReps=1,  # Number of repetitions for each trial type
    method="random",
)

# Create a file to save data
filename = f"logs/flanker_data_{subj_info['ID']}.csv"
data_file = open(filename, "w")
data_file.write("subject_id,trial_number,target,flankers,congruency,response,rt,correct\n")

# Run the experiment
trial_count = 0
for trial in trials:
    trial_count += 1

    # Set the stimuli for the current trial
    target.text = trial["target"]
    flanker_left.text = trial["flankers"]
    flanker_right.text = trial["flankers"]

    # Display the stimuli
    target.draw()
    flanker_left.draw()
    flanker_right.draw()
    win.flip()

    # Start the clock
    trial_clock = core.Clock()

    # Wait for a response
    keys = event.waitKeys(keyList=["left", "right"])

    # Record response and reaction time
    response = keys[0]
    rt = trial_clock.getTime()  # Get reaction time from the clock

    # Check if the response is correct
    correct = response == trial["correct_response"]

    # Write data to file
    data_file.write(
        f"{subj_info['ID']},{trial_count},{trial['target']},{trial['flankers']},{trial['congruency']},{response},{rt},{correct}\n"
    )

    # Clear the screen
    win.flip()

    # Inter-trial interval
    core.wait(0.5)

# Close the data file
data_file.close()

# Close the window
win.close()