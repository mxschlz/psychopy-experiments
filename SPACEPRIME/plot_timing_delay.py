import pandas as pd
import seaborn


df = pd.read_csv("C:\\Users\AC_STIM\Desktop\\spaceprime_delay.csv", delimiter="\t")
trigger_events = df[df["Keypad 1"] == 1]
sound_events = df[df["Mic 1 "] == 1]