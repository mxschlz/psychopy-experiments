from WP1.experiment_logic import WP1Session
from utils.utils import get_input_from_dict

info = get_input_from_dict({"subject_id": 99,  # enter subject id
                            "test": 1  # enter if test run (1) or not (0)
                            })

# create subject sequence
# generate_subject_sequence(subject_id=info["subject_id"])
sess = WP1Session(output_str=f'sub-{info["subject_id"]}', output_dir="WP1/logs", settings_file="WP1/config.yaml")
sess.run()
sess.quit()
