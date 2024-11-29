import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
plt.ion()


# load up datafrane
df = pd.read_csv("G:\Meine Ablage\PhD\data\BBTKv2\SPACEPRIME\\spaceprime_delay.csv", delimiter="\t")
# get only the relevant columns
df = df[["Mic 1", "Keypad 1", "Elapsed uS"]]
# transform from microseconds to milliseconds
df["Elapsed mS"] = df["Elapsed uS"] / 1000
# delete irrelevant column
df.pop("Elapsed uS")
# get the relevant indices where events occur simultaneously
indices = df[(df['Mic 1'] == 1) & (df['Keypad 1'] == 1)].index
# subtract the previous row from the row where both events occur simultaneously
onset_asynchrony = df.loc[indices, "Elapsed mS"].reset_index(drop=True) - df.loc[indices-1, "Elapsed mS"].reset_index(drop=True)
# plot the stuff
sns.displot(onset_asynchrony[onset_asynchrony < 2000])
sns.boxplot(onset_asynchrony[onset_asynchrony < 2000])
