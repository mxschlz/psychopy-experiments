import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from utils.stats import permutation_test
#import matplotlib
#matplotlib.use("Qt5Agg")
plt.ion()


# path for figure saving
figpath = "C:\PycharmProjects\psychopy-experiments\WP1\\figures"
# load up dataframe
fp = "C:\\PycharmProjects\\psychopy-experiments\\SPACEPRIME\\logs\\clean"
file_excel = os.listdir(fp)[0]
# read dataframe
df = pd.read_excel(os.path.join(fp, file_excel))
# get results only
results = df[(df['event_type'] == 'mouse_click') & (df['rt'] != 0) & (df["phase"] == 1)]
# Create a boolean mask to identify consecutive duplicates in `ITI-Jitter`
mask = results['ITI-Jitter'] != results['ITI-Jitter'].shift(1)

# Filter the DataFrame to keep only the unique rows
df_filtered = results[mask].copy()

# Display the shape of the original and filtered DataFrames
print(f"Original DataFrame shape: {results.shape}")
print(f"Filtered DataFrame shape: {df_filtered.shape}")
# singleton absent versus present percentage correct
plot = sns.barplot(data=df_filtered, x="SingletonPresent", y="iscorrect", hue="block")
plt.close()
# singleton absent versus present reaction time
sns.barplot(data=df_filtered, x="SingletonPresent", y="rt", hue="subject_id")
plt.close()
# spatial priming is_correct
sns.barplot(data=results, y=results.iscorrect, hue=results.SpatialPriming)
plt.close()
# spatial priming reaction time
sns.barplot(data=results, y=results.rt, hue=results.SpatialPriming)
plt.close()

# same shit with identity priming
sns.barplot(data=results, y=results.iscorrect, hue=results.IdentityPriming)
plt.close()
# identity priming reaction time
sns.barplot(data=results, y=results.rt, hue=results.IdentityPriming)
plt.close()


barplot = sns.barplot(data=results, x="TargetLoc", y="iscorrect")