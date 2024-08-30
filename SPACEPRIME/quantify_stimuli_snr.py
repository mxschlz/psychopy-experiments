import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
plt.ion()

seq_fp = "C:\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_0_snr.xlsx"

df = pd.read_excel(seq_fp)
mosaic = """
ab
cc
"""
fig, ax = plt.subplot_mosaic(mosaic, figsize=(8, 6))
sns.boxplot(data=df, x="signal_loc", y="snr_left", ax=ax["a"])
ax["a"].set_title('SNR Left')
sns.boxplot(data=df, x="signal_loc", y="snr_right", ax=ax["b"])
ax["b"].set_title('SNR Right')

df['snr_mean_both_ears'] = df[['snr_left', 'snr_right']].mean(axis=1)
sns.boxplot(data=df, x="signal_loc", y="snr_mean_both_ears", ax=ax["c"])
ax["b"].set_title('SNR Right')

plt.tight_layout()
plt.savefig("C:\\figures\\snr_both_ears.pdf", dpi=400)
