import pandas as pd
import os
from utils.utils import get_input_from_dict
from datetime import datetime
import yaml
os.chdir("C:\\Users\Max\PycharmProjects\psychopy-experiments\SPACECUE")

# get subject info
info = get_input_from_dict({"subject_id": 99,
                            "gender": "m",
                            "handedness": "r",
                            "age": 0})

# load settings
settings_path = "config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)


# some filepaths
fp = os.path.join(os.getcwd(), "logs")
fp_clean = os.path.join(fp, "clean")
results_path = os.path.join("results")
# get files in log dir
fn = [x for x in os.listdir(fp) if f'sub-{info["subject_id"]}' in x]
file_format = "events.csv"
fn = [x for x in fn if file_format in x]
if len(fn) > 1:
    files = []
    for file in fn:
        files.append(pd.read_csv(os.path.join(fp, file)))
    df = pd.concat(files, ignore_index=True)
elif len(fn) == 1:
    file = fn[0]
    df = pd.read_csv(os.path.join(fp, file))
else:
    print("Could not find any excel files!")
# sort for mouse clicks
df = df[(df["event_type"]=="key_press")]
# some cleaning
df.response = pd.to_numeric(df.response, errors='coerce')
# delete non numerical space entries
df.loc[df["response"] == "space", "response"] = 999
# make responses numerical
df.response = df.response.dropna().astype(int)
# get correct in singleton absent vs present trials
df["select_target"] = df.response == df.TargetDigit
df["select_distractor"] = df["response"] == df["SingletonDigit"]
df["select_control"] = (df["response"] == df["Non-Singleton2Digit"]) | (df["response"] == df["Non-Singleton1Digit"])
df["select_other"] = (df["response"] != df["Non-Singleton2Digit"]) & (df["response"] != df["Non-Singleton1Digit"]) & (df["response"] != df["TargetDigit"]) & (df["response"] != df["SingletonDigit"])
# add meta data
df["gender"] = 1 if info["gender"] == "f" else 0
df["handedness"] = 1 if info["handedness"] == "r" else 0
df["age"] = info["age"]
# get absolute trial_nr count
df['absolute_trial_nr'] = (df['block']) * (df["trial_nr"].max() + 1) + df['trial_nr']
# Find duplicate trial numbers
duplicates = df[df.duplicated(subset='absolute_trial_nr', keep=False)]
print("Duplicate trial numbers:\n", duplicates)
# drop duplicates
df = df.drop_duplicates(subset='absolute_trial_nr', keep='first')  # or 'last'
# Create a new DataFrame to store aligned behavioral data
df = df.set_index('absolute_trial_nr')
# Create a complete range of trial numbers
all_trials = pd.RangeIndex(start=0, stop=settings["session"]["n_trials"]*settings["session"]["n_blocks"], step=1, name='absolute_trial_nr')
# Reindex the DataFrame with the complete range
df = df.reindex(all_trials)
# save dataframe
df.to_csv(os.path.join(fp_clean, f"{file.split('_')[0]}_clean_{datetime.now().strftime('%B_%d_%Y_%H_%M_%S')}.csv"),
          index=False)
print("Done! :)")
