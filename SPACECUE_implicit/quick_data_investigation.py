import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use("TkAgg")
plt.ion()


# load up dataframe
fp = "C:\\Users\\Max\\PycharmProjects\\psychopy-experiments\\SPACECUE_implicit\\logs\\clean"
file_excel = "sci-98_clean_October_09_2025_16_52_43.csv"
# read dataframe
df = pd.read_csv(os.path.join(fp, file_excel))
df = df[df["phase"]!= 2]

# singleton absent versus present percentage correct
sns.barplot(data=df, x="DistractorProb", y="select_target", order=[])
