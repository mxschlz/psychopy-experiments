from experiment_logic import SpaceprimeSession


# create subject sequence
# generate_subject_sequence(subject_id=info["subject_id"])
sess = SpaceprimeSession(output_str=f'sub-102', output_dir="logs",
                         settings_file="config.yaml",
                         starting_block=1, test=True)
sess.bbtkv2_test_run(n_trials=20)