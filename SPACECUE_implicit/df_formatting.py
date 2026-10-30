import pandas as pd
from utils.utils import get_input_from_dict
from datetime import datetime
from pathlib import Path
import os
import yaml
#os.chdir("C:\\Users\Max\PycharmProjects\psychopy-experiments\SPACECUE_implicit")

# get subject info
info = get_input_from_dict({"subject_id": 99,
                            "gender": "m",
                            "handedness": "r",
                            "age": 0})

subject_id = int(info["subject_id"])

# load settings
settings_path = Path("config.yaml")
with open(settings_path) as file:
    settings = yaml.safe_load(file)


# some filepaths
project_root = Path(settings["filepaths"]["project"])
fp = project_root / "logs"
fp_clean = fp / "clean"
fp_clean.mkdir(parents=True, exist_ok=True)  # Ensure the clean directory exists
# get files in log dir
fn = list(fp.glob(f'sci-{subject_id}*events.csv'))
if len(fn) > 1:
    files = []
    for file in fn:
        files.append(pd.read_csv(file))
    df = pd.concat(files, ignore_index=True)
elif len(fn) == 1:
    file = fn[0]
    df = pd.read_csv(os.path.join(fp, file))
else:
    print("Could not find any excel files!")
# 1. Base trial structure on stimulus presentations (retains all 1800 trials)
stims = df[df["event_type"] == "stim"].copy()
stims['Absolute Trial Nr'] = (stims['block']) * (stims["trial_nr"].max() + 1) + stims['trial_nr']
stims = stims.drop_duplicates(subset='Absolute Trial Nr', keep='last')

# 2. Extract mouse clicks
clicks = df[df["event_type"] == "mouse_click"].copy()
clicks['Absolute Trial Nr'] = (clicks['block']) * (clicks["trial_nr"].max() + 1) + clicks['trial_nr']
clicks = clicks.drop_duplicates(subset='Absolute Trial Nr', keep='first')

# Clean up click response column
clicks['response'] = pd.to_numeric(clicks['response'], errors='coerce')

# 3. Left-join mouse clicks onto stimulus trials
df = pd.merge(
    stims,
    clicks[['Absolute Trial Nr', 'response', 'rt']],
    on='Absolute Trial Nr',
    how='left',
    suffixes=('', '_click')
)
df['response'] = df['response_click']
df['rt'] = df['rt_click']
df.drop(columns=['response_click', 'rt_click'], inplace=True, errors='ignore')

# swap distractor probabilities for subjects 996 and 989
if subject_id in [996, 989]:
    swap_dict = {'high-probability': 'low-probability', 'low-probability': 'high-probability'}
    df['DistractorProb'] = df['DistractorProb'].map(swap_dict)

# get correct in singleton absent vs present trials (False on non-click trials)
df["IsCorrect"] = (df['response'] == df['TargetDigit'])
df["SelectDistractor"] = (df['response'] == df['SingletonDigit'])
df["SelectControl"] = (df['response'] == df['Non-Singleton2Digit']) | (df['response'] == df['Non-Singleton1Digit'])
df["SelectOther"] = df['response'].notna() & (~df['IsCorrect']) & (~df['SelectDistractor']) & (~df['SelectControl'])

# add meta data
df["Gender"] = "Female" if info["gender"] == "f" else "Male"
df["Handedness"] = "Right-handed" if info["handedness"] == "r" else "Left-handed"
df["age"] = info["age"]

# Create a new DataFrame to store aligned behavioral data
df = df.set_index('Absolute Trial Nr')
# Create a complete range of trial numbers
all_trials = pd.RangeIndex(start=0, stop=settings["session"]["n_trials"]*settings["session"]["n_blocks"], step=1, name='Absolute Trial Nr')
# Reindex the DataFrame with the complete range
df = df.reindex(all_trials)
# Reformat trial_nr column to nullable integer type to handle NaNs from reindexing
df["Trial Nr"] = df["trial_nr"].astype('Int64')
df["Phase"] = df["phase"].astype('Int64')
df["SingletonPresent"] = df["SingletonPresent"].astype(bool)
locations_map = {1:"Left", 2:"Front", 3:"Right", 0:"Not present"}
df["TargetLoc"] = df["TargetLoc"].map(locations_map, na_action='ignore')
df["SingletonLoc"] = df["SingletonLoc"].map(locations_map, na_action='ignore')
df["Non-Singleton1Loc"] = df["Non-Singleton1Loc"].map(locations_map, na_action='ignore')
df["Non-Singleton2Loc"] = df["Non-Singleton2Loc"].map(locations_map, na_action='ignore')
priming_map = {0:"No priming", -1:"Negative priming", 1:"Positive priming"}
df["Priming"] = df["Priming"].map(priming_map, na_action='ignore')
df["Block"] = df["block"].astype('Int64')
df["Subject ID"] = df["subject_id"].astype('Int64')
df["Age"] = df["age"].astype('Int64')

# swap 990 and 900 for switching HP distractor location design
if subject_id in [990]:
    df["Subject ID"] = 900

# Drop original columns that have been renamed or are no longer needed
columns_to_drop = [
    'trial_nr', 'phase', 'block', 'subject_id', 'age'
]
df = df.drop(columns=columns_to_drop)

# save dataframe
df.to_csv(fp_clean / f"{Path(file).stem.split('_')[0]}_clean_{datetime.now().strftime('%B_%d_%Y_%H_%M_%S')}.csv",
          index=False)
print("Done! :)")
