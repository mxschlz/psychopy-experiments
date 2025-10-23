import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib
plt.ion()


# load up dataframe
fp = "D:\MSchulz\SPACECUE_implicit\logs\clean"
file_excel = "sci-998_clean_October_22_2025_17_28_44.csv"
# read dataframe
df = pd.read_csv(os.path.join(fp, file_excel))
df = df[df["phase"]!= 2]

# singleton absent versus present percentage correct
sns.barplot(data=df, x="DistractorProb", y="select_target", order=[])
