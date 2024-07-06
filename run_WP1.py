from WP1.experiment_logic import WP1Session
from utils.utils import get_input_from_dict

info = get_input_from_dict({"subject_id": 99,  # enter subject id
                            "test": True,  # enter if test run (1) or not (0)
                            "block": 0})

# create subject sequence
# generate_subject_sequence(subject_id=info["subject_id"])
sess = WP1Session(output_str=f'sub-{info["subject_id"]}', output_dir="SPACEPRIME/logs", settings_file="SPACEPRIME/config.yaml",
                  starting_block=info["block"], test=True if info["test"] == 1 else False)
sess.run()
sess.quit()
