import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
#import matplotlib
#matplotlib.use("Qt5Agg")
plt.ion()


# path for figure saving
# load up dataframe
fp = "SPACECUE\logs"
file_excel = "sub-01_May_20_2025_09_27_32_events.csv"
# read dataframe
results = pd.read_csv(os.path.join(fp, file_excel))

# Display the shape of the original and filtered DataFrames
print(f"Original DataFrame shape: {results.shape}")
# singleton absent versus present percentage correct
plot = sns.barplot(data=results, x="SingletonPresent", y="iscorrect", hue="block")
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


barplot = sns.barplot(data=results, x="TargetLoc", y="iscorrect")