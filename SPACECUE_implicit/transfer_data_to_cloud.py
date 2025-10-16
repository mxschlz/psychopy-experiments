import os
from utils.utils import get_input_from_dict
import shutil
import glob


# define subject id
info = get_input_from_dict({"subject_id": 99})
# TRANSFER CLEAN BEHAVIOR
print("Copying clean data ...")
# Create the destination directory if it doesn't exist
destination_dir_clean = f'G:\\Meine Ablage\\PhD\\data\\SPACECUE_implicit\\derivatives\\preprocessing\\sci-{info["subject_id"]}\\beh'
print(f"Creating directory {destination_dir_clean}")
os.makedirs(destination_dir_clean, exist_ok=True)  # create directory no matter if it already exists
# get source dir
source_dir_clean = "../SPACECUE_implicit/logs/clean"
# get source path
glob_file = os.path.join(source_dir_clean, f'sci-{info["subject_id"]}_clean*.csv')
glob_file_clean = glob.glob(glob_file)[0].split("\\")[2]
destination_path_clean = os.path.join(destination_dir_clean, glob_file_clean)
filename_clean = os.path.join(source_dir_clean, glob_file_clean)
print(f"Transferring file {filename_clean} to {destination_path_clean}")
shutil.copy(filename_clean, destination_path_clean)
# TRANSFER RAW BEHAVIOR
print("Copying raw data ...")
# Create the destination directory if it doesn't exist
destination_dir_raw = f'G:\\Meine Ablage\\PhD\\data\\SPACECUE_implicit\\sourcedata\\raw\\sci-{info["subject_id"]}\\beh'
print(f"Creating directory {destination_dir_raw}")
os.makedirs(destination_dir_raw, exist_ok=True)  # create directory no matter if it already exists
# get source dir
source_dir_raw = "../SPACECUE_implicit/logs"
# move all files from that directory to destination
for file in os.listdir(source_dir_raw):
	if f'sci-{info["subject_id"]}' in file:
		source_path_raw = os.path.join(source_dir_raw, file)
	else:
		continue
	destination_path_raw = os.path.join(destination_dir_raw, file)
	if os.path.isfile(source_path_raw):
		print(f"Transferring {source_path_raw} to {destination_path_raw}")
		shutil.copy(source_path_raw, destination_path_raw)
try:
	# TRANSFER FLANKER BEHAVIOR
	print("Copying flanker data ...")
	# Create the destination directory if it doesn't exist
	destination_dir_flanker = f'G:\\Meine Ablage\\PhD\\data\\SPACECUE_implicit\\sourcedata\\raw\\sci-{info["subject_id"]}\\beh'
	print(f"Creating directory {destination_dir_flanker}")
	os.makedirs(destination_dir_flanker, exist_ok=True)  # create directory no matter if it already exists
	# get source dir
	source_dir_flanker = "../SPACECUE_implicit/logs"
	# get source path
	glob_file_flanker = os.path.join(source_dir_flanker, f'flanker_data_{info["subject_id"]}*.csv')
	glob_file_clean_flanker = glob.glob(glob_file_flanker)[0].split("\\")[1]
	destination_path_clean_flanker = os.path.join(destination_dir_flanker, glob_file_clean_flanker)
	filename_clean_flanker = os.path.join(source_dir_flanker, glob_file_clean_flanker)
	print(f"Transferring file {filename_clean_flanker} to {destination_path_clean_flanker}")
	shutil.copy(filename_clean_flanker, destination_path_clean_flanker)
except IndexError:
	print(f"No flanker data found for subject {info['subject_id']}.")
try:
	# TRANSFER QUESTIONNAIRES
	print("Copying questionnaire data ...")
	# Create the destination directory if it doesn't exist
	destination_dir_questionnaire = f'G:\\Meine Ablage\\PhD\\data\\SPACECUE_implicit\\sourcedata\\raw\\sci-{info["subject_id"]}\\questionnaires'
	print(f"Creating directory {destination_dir_questionnaire}")
	os.makedirs(destination_dir_questionnaire, exist_ok=True)  # create directory no matter if it already exists
	# get source dir
	source_dir_questionnaire = "logs\\questionnaires"
	# get source path
	glob_file_questionnaire = os.path.join(source_dir_questionnaire, f'*{info["subject_id"]}*.csv')
	for i in range(2):  # 2 questionnaires
		glob_file_clean_questionnaire = glob.glob(glob_file_questionnaire)[i].split("\\")[2]
		destination_path_clean_questionnaire = os.path.join(destination_dir_questionnaire, glob_file_clean_questionnaire)
		filename_clean_questionnaire = os.path.join(source_dir_questionnaire, glob_file_clean_questionnaire)
		print(f"Transferring file {filename_clean_questionnaire} to {destination_path_clean_questionnaire}")
		shutil.copy(filename_clean_questionnaire, destination_path_clean_questionnaire)
except IndexError:
	print(f"No questionnaire data found for subject {info['subject_id']}.")
# TRANSFER TRIAL SEQUENCES
print("Copying trial sequences ...")
# Create the destination directory if it doesn't exist
destination_dir_sequences = f'G:\\Meine Ablage\\PhD\\data\\SPACECUE_implicit\\sequences\\sci-{info["subject_id"]}'
print(f"Creating directory {destination_dir_sequences}")
os.makedirs(destination_dir_sequences, exist_ok=True)  # create directory no matter if it already exists
# get source dir
source_dir_sequences = "../SPACECUE_implicit/sequences"
# get source path
# move all files from that directory to destination
for file in os.listdir(source_dir_sequences):
	if f'sci-{info["subject_id"]}' in file:
		source_path_sequences = os.path.join(source_dir_sequences, file)
	else:
		continue
	destination_path_sequences = os.path.join(destination_dir_sequences, file)
	print(f"Transferring {source_path_sequences} to {destination_path_sequences}")
	if os.path.isfile(source_path_sequences):
		shutil.copy(source_path_sequences, destination_path_sequences)
	elif os.path.isdir(source_path_sequences):
		shutil.copytree(source_path_sequences, destination_path_sequences)
