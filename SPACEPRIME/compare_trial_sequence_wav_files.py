import slab
import pandas as pd
import os


# load wav files
sounds = []
wav_dir = "C:\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_0"
for wav_file in os.listdir(wav_dir):
    sounds.append(slab.Sound.read(os.path.join(wav_dir, wav_file)))

csv_file = pd.read_excel("C:\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_0.xlsx")

for i, row in csv_file.iterrows():
    print(f"Playing trial {i}")
    print(f"Playing sound: {row}")
    sounds[i].play()
    input("Press Enter to continue...")
