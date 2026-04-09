import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import matplotlib
plt.ion()


# load up dataframe
fp = "C:\\Users\\Max\\PycharmProjects\\psychopy-experiments\\SPACECUE_implicit\\logs"
file_excel = "sci-99_February_11_2026_13_26_02_events.csv"
# read dataframe
df = pd.read_csv(os.path.join(fp, file_excel))

# singleton absent versus present percentage correct
sns.barplot(data=df, x="DistractorProb", y="select_target", order=[])
