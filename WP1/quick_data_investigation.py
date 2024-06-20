import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from utils.stats import permutation_test
import matplotlib
matplotlib.use("Qt5Agg")
plt.ion()
sns.set_theme("poster", palette="husl")

# path for figure saving
figpath = "C:\PycharmProjects\psychopy-experiments\WP1\\figures"
# load up dataframe
fp = "C:\\PycharmProjects\\psychopy-experiments\\WP1\\results\\"
file_excel = os.listdir(fp)[0]
# read dataframe
df = pd.read_excel(os.path.join(fp, file_excel), index_col=0)
# get results only
results = df[(df['event_type'] == 'response') & (df['rt'] != 0)]
# singleton absent versus present percentage correct
plot = sns.barplot(data=results, x="SingletonPresent", y="iscorrect", hue="subject_id")
plt.close()
# singleton absent versus present reaction time
sns.barplot(data=results, x="SingletonPresent", y="rt", hue="subject_id")
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
