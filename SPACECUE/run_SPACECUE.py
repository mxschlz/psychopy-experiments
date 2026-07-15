from experiment_logic import SpaceCueSession
from utils.utils import get_input_from_dict


# 1. get info from a dialog window
info = get_input_from_dict({"subject_id": 1,  # enter subject id
                            "test": True,  # enter if test run (1) or not (0)
                            "block": 0,
                            "age": 20,
                            "gender": ["m", "w", "d"],
                            "handedness": ["r", "l"]})
# 2. Instantiate the session
sess = SpaceCueSession(output_str=f'sce-{info["subject_id"]}', output_dir="logs",
                         settings_file="config.yaml",
                         starting_block=info["block"], test=True if info["test"] == 1 else False,
                         demographics={"age": info["age"], "gender": info["gender"], "handedness": info["handedness"]})
# 3. Run the session
sess.run(starting_block=info["block"])
# 4. Close the session
sess.close()
# 5. Quit the session
sess.quit()
