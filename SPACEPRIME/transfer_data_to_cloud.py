import os
from utils.utils import get_input_from_dict


info = get_input_from_dict({"subject_id": 99})

# Create the destination directory if it doesn't exist
destination_dir = f'G:\\Meine Ablage\\PhD\\data\\SPACEPRIME\\derivatives\\preprocessing\\sub-{info["subject_id"]}\\beh'
os.makedirs(destination_dir, exist_ok=True)
# get source path
source_path = f'logs\clean\sub-{info["subject_id"]}_clean.csv'