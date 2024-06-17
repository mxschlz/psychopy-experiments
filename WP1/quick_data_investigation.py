import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
plt.ion()


df = pd.read_excel("C:\PycharmProjects\psychopy-experiments\WP1\logs//40 Hz Target\sub-99_June_17_2024_11_24_20_events.xlsx")
df = df.fillna(0)

# get correct in singleton absent vs present trials
df["iscorrect"] = df.response == df.TargetDigit

results = df[(df['response'] != 0) & (df['event_type'] == 'response')]

sns.barplot(data=results, y=results.iscorrect, hue=results.SingletonPresent)
