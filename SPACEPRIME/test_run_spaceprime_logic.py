from SPACEPRIME.experiment_logic import SpaceprimeSession


# instantiate session
sess = SpaceprimeSession(output_str=f'sub-105', output_dir="logs",
                         settings_file="config.yaml",
                         starting_block=0, test=True)
#sess.win.close()
# set block
sess.set_block(block=1)
# load up trial sequence
sess.load_sequence()
# create trials from sequence
sess.create_trials(n_trials=5,
                   durations=(sess.settings["session"]["stimulus_duration"],
                              sess.settings["session"]["response_duration"],
                              None),  # this is hacky and usually not recommended (for ITI Jitter)
                   timing=sess.settings["session"]["timing"])
# set up timer etc. for the experiment
sess.start_experiment()
# run through trials
for trial in sess.trials:
    trial.trigger_name = "test_trigger"
    # play sound
    trial.run()
# clean up
sess.close()
sess.quit()
