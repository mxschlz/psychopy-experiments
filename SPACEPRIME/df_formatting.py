import pandas as pd
import os
import datetime
from utils.utils import get_input_from_dict

# print(os.getcwd())
# get current date with seconds to make it unique
date = datetime.datetime.now().strftime('%B_%d_%Y_%H_%M_%S')
# get subject info
info = get_input_from_dict({"subject_id": 99})
# some filepaths
fp = os.path.join(os.getcwd(), "logs")
fp_clean = os.path.join(fp, "clean")
results_path = os.path.join("results")
# get files in log dir
fn = [x for x in os.listdir(fp) if f'sub-{info["subject_id"]}' in x]
# filter for excel files
fn = [x for x in fn if ".csv" in x]
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
# some cleaning
df.response = pd.to_numeric(df.response, errors='coerce')
df = df.fillna(0)
# delete non numerical space entries
df.loc[df["response"] == "space", "response"] = 999
# make responses numerical
df.response = df.response.astype(int)
# get correct in singleton absent vs present trials
df["iscorrect"] = df.response == df.TargetDigit
# save dataframe

df.to_csv(os.path.join(fp_clean, f"{file.split('_')[0]}_clean.csv"), index=False)

# concatenate
dfs = []
# load up dataframe
for file in os.listdir(fp_clean):
    if ".csv" in file:
        dfs.append(pd.read_csv(os.path.join(fp_clean, file)))
df = pd.concat(dfs, ignore_index=False)
# df.pop("Unnamed: 0")
df.to_csv(os.path.join(results_path, f"results_{date}.csv"))

print("Done! :)")