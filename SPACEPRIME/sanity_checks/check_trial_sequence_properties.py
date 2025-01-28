import pandas as pd


dfs = [pd.read_csv(f"C:\\Users\Max\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_{block}.csv") for block in range(10)]
df = pd.concat(dfs)

# check proportions of c, np and pp trials
nr_c = 0
nr_pp = 0
nr_np = 0
# check proportion of singleton present trials
nr_sp = 0
previous_target = None
previous_distractor = None
previous_control = None

for i, row in df.iterrows():
    nr_sp += row["SingletonPresent"]
    if row["TargetDigit"] == previous_distractor:
        nr_np += 1
    elif row["TargetDigit"] == previous_target:
        nr_pp += 1
    else:
        nr_c += 1
    if row["SingletonPresent"]:
        previous_control = row["Non-Singleton2Digit"]
    previous_target = row["Target"]
