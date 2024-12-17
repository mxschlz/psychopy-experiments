from SPACEPRIME.experiment_logic import SpaceprimeSession
from psychopy import core


# create subject sequence
# generate_subject_sequence(subject_id=info["subject_id"])
sess = SpaceprimeSession(output_str=f'sub-999', output_dir="../SPACEPRIME/logs", settings_file="SPACEPRIME/config.yaml",
                         starting_block=0, test=True)
sess.set_block(block=4)  # intentionally choose block within
sess.load_sequence()
sess.create_trials(n_trials=15,
                   durations=(sess.settings["session"]["stimulus_duration"],
                              sess.settings["session"]["response_duration"],
                              None),
                   timing=sess.settings["session"]["timing"])
sess.start_experiment()
sess.win.close()
for trial in sess.trials:
    core.wait(1)
    trial.send_trig_and_sound()
    core.wait(1)

sess.close()
sess.quit()

import slab
sound = slab.Sound(trial.stim.data[:, 0], samplerate=44100)
