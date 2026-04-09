import os
os.environ["SD_ENABLE_ASIO"] = "1"
import sounddevice as sd
from experiment_logic import SpacecueImplicitSession
from utils.utils import get_input_from_dict


info = get_input_from_dict({"subject_id": 99,  # enter subject id
                            "test": True,  # enter if test run (1) or not (0)
                            "block": 0})

# Force the subject_id and block to be integers to strip leading zeros
# and perfectly match the output from generate_subject_sequence.py
subject_id = int(info["subject_id"])
block = int(info["block"])

# create subject sequence
# generate_subject_sequence(subject_id=info["subject_id"])
sess = SpacecueImplicitSession(output_str=f'sci-{subject_id}', output_dir="logs",
                         settings_file="config.yaml",
                         starting_block=block, test=True if info["test"] == 1 else False)
# run
sess.run(starting_block=info["block"])
# close
sess.close()
# quit
sess.quit()
