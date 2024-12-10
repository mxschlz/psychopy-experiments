import os
from utils.utils import get_input_from_dict
import shutil


# define subject id
info = get_input_from_dict({"subject_id": 99})
# TRANSFER CLEAN BEHAVIOR
print("Copying clean data ...")
# Create the destination directory if it doesn't exist
destination_dir_clean = f'G:\\Meine Ablage\\PhD\\data\\SPACEPRIME\\derivatives\\preprocessing\\sub-{info["subject_id"]}\\beh'
print(f"Creating diriectory {destination_dir_clean}")
os.makedirs(destination_dir_clean, exist_ok=True)  # create directory no matter if it already exists
# get source dir
source_dir_clean = "logs\\clean"
# get source path
source_path_clean = os.path.join(source_dir_clean, f'sub-{info["subject_id"]}_clean.csv')
destination_path_clean = os.path.join(destination_dir_clean, f'sub-{info["subject_id"]}_clean.csv')
print(f"Transferring file {source_path_clean} to {destination_path_clean}")
shutil.copy(source_path_clean, destination_path_clean)
# TRANSFER RAW BEHAVIOR
print("Copying raw data ...")
# Create the destination directory if it doesn't exist
destination_dir_raw = f'G:\\Meine Ablage\\PhD\\data\\SPACEPRIME\\sourcedata\\raw\\sub-{info["subject_id"]}\\beh'
print(f"Creating directory {destination_dir_raw}")
os.makedirs(destination_dir_raw, exist_ok=True)  # create directory no matter if it already exists
# get source dir
source_dir_raw = "logs"
# move all files from that directory to destination
for file in os.listdir(source_dir_raw):
	if f'sub-{info["subject_id"]}' in file:
		source_path_raw = os.path.join(source_dir_raw, file)
	else:
		continue
	destination_path_raw = os.path.join(destination_dir_raw, file)
	if os.path.isfile(source_path_raw):
		print(f"Transferring {source_path_raw} to {destination_path_raw}")
		shutil.copy(source_path_raw, destination_path_raw)
