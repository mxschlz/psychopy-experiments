import pandas as pd
import os
import datetime

date = datetime.datetime.now().strftime('%B_%d_%Y_%H_%M_%S')

# load up dataframe
fp = "C:\PycharmProjects\psychopy-experiments\WP1\logs"
fn = "sub-02_June_20_2024_12_48_11_events.xlsx"
fp_clean = fp + "\clean"
results_path = "C:\PycharmProjects\psychopy-experiments\WP1\\results"
# load dataframe
df = pd.read_excel(os.path.join(fp, fn))
# some cleaning
df = df.fillna(0)
# delete non numerical space entries
for i, row in df.iterrows():
    if row.response == "space":
        df.response.iloc[i] = 999
# make responses numerical
df.response = df.response.astype(int)
# get correct in singleton absent vs present trials
df["iscorrect"] = df.response == df.TargetDigit
# save dataframe
df.to_excel(os.path.join(fp_clean, fn))

# concatenate
dfs = []
# load up dataframe
for file in os.listdir(fp_clean):
    df = pd.read_excel(os.path.join(fp_clean, file), index_col=0)
    dfs.append(pd.read_excel(os.path.join(fp_clean, file), index_col=0))
df = pd.concat(dfs, ignore_index=True)
df.pop("Unnamed: 0")
df.to_excel(os.path.join(results_path, f"results_{date}.xlsx"))
