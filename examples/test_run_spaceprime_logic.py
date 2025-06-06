from SPACEPRIME.experiment_logic import SpaceprimeSession


# instantiate session
sess = SpaceprimeSession(output_str=f'sub-105', output_dir="../SPACEPRIME/logs",
                         settings_file="../SPACEPRIME/config.yaml",
                         starting_block=0, test=True)
# run testing function
sess.bbtkv2_test_run(n_trials=50)