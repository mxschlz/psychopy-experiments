from SPACEPRIME.experiment_logic import SpaceprimeSession
from utils.utils import get_input_from_dict

info = get_input_from_dict({"subject_id": 999,  # enter subject id
                            "test": True,  # enter if test run (1) or not (0)
                            "block": 0})

# create subject sequence
# generate_subject_sequence(subject_id=info["subject_id"])
sess = SpaceprimeSession(output_str=f'sub-{info["subject_id"]}', output_dir="logs",
                         settings_file="config.yaml",
                         starting_block=info["block"], test=True if info["test"] == 1 else False)
sess.run()
sess.quit()
