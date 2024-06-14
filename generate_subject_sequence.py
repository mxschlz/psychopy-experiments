import io

import pandas as pd
import numpy as np
import yaml
import slab
from WP1.space_encoding import SPACE_ENCODER
from utils.signal_processing import lateralize, externalize
import argparse
import sys
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the project root directory (one level up) to Python's search path
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

parser = argparse.ArgumentParser(description='Generate subject sequence')
parser.add_argument('--subject_id', "-s", type=int, help='Subject ID (integer)', default=99)
args = parser.parse_args()
sub_id = args.subject_id


def precompute_sequence(subject_id, settings):
    subject_id = '0' + str(subject_id) if subject_id < 10 else str(subject_id)

    if any(str(subject_id) in s for s in os.listdir("WP1/sequences")):
        raise FileExistsError(f"Sequences for sub-{subject_id} has already been created! "
                              f"Please check your sequence directory.")

    n_trials = settings["session"]["n_trials"]
    df = pd.read_excel(f"WP1/all_combinations_{settings['session']['n_locations']}"
                       f"_loudspeakers_{settings['session']['n_digits']}_digits.xlsx")

    # make copy
    df_copy = df.copy()

    n_blocks = settings["session"]["n_blocks"]

    for block in range(n_blocks):
        # save block sequence as .zip file
        filename = f"WP1/sequences/sub-{subject_id}_block_{block}"
        try:
            os.mkdir(filename)
        except FileExistsError:
            print(f"Directory {filename} already exists")
            return
        # hopefully not loop into eternity ...
        while True:
            print(f"Generating trial sequences for subject_id {subject_id}, block {block} ... ", end="\r")
            # Filter the dataframe to include only rows where `SingletonPresent` is True
            singleton_trials = df_copy[df_copy['SingletonPresent'] == True].sample(n=int(n_trials/2))

            # Filter the dataframe to include only rows where `SingletonPresent` is False
            non_singleton_trials = df_copy[df_copy['SingletonPresent'] == False].sample(n=int(n_trials/2))

            # randomly merge singleton trials and nonsingleton trials together
            merged = pd.concat([singleton_trials, non_singleton_trials]).sample(frac=1).reset_index(drop=True)

            # Shift the rows of the copied dataframe down by 1
            df_shifted = merged.shift(1)

            # Join the shifted dataframe back to the original dataframe
            df_combined = merged.join(df_shifted, rsuffix='_previous')

            # use numerical values for priming encoding --> 1 = positive, -1 = negative, 0 = no priming
            df_combined['SpatialPriming'] = np.nan
            df_combined['IdentityPriming'] = np.nan

            # Iterate over rows
            for i, row in df_combined.iterrows():
                if row["TargetDigit"] == row["SingletonDigit_previous"]:  # negative identity priming
                    df_combined.loc[i, "IdentityPriming"] = -1
                if row["SingletonDigit"] == row["TargetDigit_previous"]:  # positive identity priming
                    df_combined.loc[i, "IdentityPriming"] = 1
                if row["TargetLoc"] == row["SingletonLoc_previous"]:  # negative spatial priming
                    df_combined.loc[i, "SpatialPriming"] = -1
                if row["SingletonLoc"] == row["TargetLoc_previous"]:  # positive spatial priming
                    df_combined.loc[i, "SpatialPriming"] = 1

            # check for roughly equal amount of priming cases
            if (np.abs(np.diff(df_combined.groupby("IdentityPriming").size().values)) > 0
                    or np.abs(np.diff(df_combined.groupby("SpatialPriming").size().values)) > 0):
                print("Difference between priming conditions too large. Resampling ...", end="\r")
            else:
                if (df_combined.groupby("IdentityPriming").size().values[0] +
                        df_combined.groupby("SpatialPriming").size().values[0] > 0.2 * len(df_combined)):
                    print(df_combined.groupby('IdentityPriming').size())
                    print(df_combined.groupby('SpatialPriming').size())
                    break
                else:
                    continue

        # drop unnecessary columns
        cols_to_drop = df_combined.columns[df_combined.columns.str.contains('previous')]

        # some further cleaning
        df_combined.drop(cols_to_drop, axis=1, inplace=True)
        df_final = df_combined.fillna(0).astype(int)

        # Save the block with a distinctive name
        print(f"Singleton trial block length: {df_final[df_final['SingletonPresent'] == True].__len__()}")
        print(f"Non Singleton trial block length: {df_final[df_final['SingletonPresent'] == False].__len__()}")
        print(f"Saving block with size {len(df_final)} ... ")
        file_name = f"WP1/sequences/sub-{subject_id}_block_{block}.xlsx"
        df_final.to_excel(file_name, index=False)  # Save as CSV, excluding the row index

        print(f"Precomputing trial sounds for subject {subject_id}, block {block} ... ", end="\r")
        sound_sequence = []

        # load sounds
        singletons = [slab.Sound.read(f"stimuli/distractors_{settings['session']['distractor_type']}/{x}")
                       for x in os.listdir(f"stimuli/distractors_{settings['session']['distractor_type']}")]
        targets = [slab.Sound.read(f"stimuli/targets/{x}") for x in os.listdir(f"stimuli/targets")]
        others = [slab.Sound.read(f"stimuli/digits_all_250ms/{x}") for x in os.listdir(f"stimuli/digits_all_250ms")]

        # binauralize
        singletons = [slab.Binaural(data=x) for x in singletons]
        targets = [slab.Binaural(data=x) for x in targets]
        others = [slab.Binaural(data=x) for x in others]

        # retrieve sound level to adjust sounds to
        soundlvl = settings["session"]["level"]

        for i, row in df_final.iterrows():
            print(f"Precompute trialsound for trial {i}, block {block} ... ", end="\r")
            # make trial sound container
            trialsound = slab.Binaural.silence(duration=settings["session"]["stimulus_duration"],
                                             samplerate=settings["session"]["samplerate"])
            # get targets
            targetval = row["TargetDigit"]
            targetsound = targets[targetval - 1]
            targetsound.level = soundlvl  # adjust level
            targetloc = row["TargetLoc"]  # get target location
            azimuth, ele = SPACE_ENCODER[targetloc]  # get coords
            targetsound_lateralized = lateralize(sound=targetsound, azimuth=azimuth)  # ITD and ILD
            targetsound_rendered = externalize(targetsound_lateralized, azi=azimuth, ele=ele)  # add HRTF
            if targetsound_rendered.data.shape != trialsound.data.shape:
                samplediff = targetsound_rendered.data.shape[0] - trialsound.data.shape[0]
                targetsound_rendered.data = targetsound_rendered[:-samplediff]
            trialsound.data += targetsound_rendered.data  # add to trial sound

            if row["SingletonPresent"] == 1:
                print(f"Singleton present in trial {i}. Computing sound mixture ... ", end="\r")
                # singleton
                singletonval = row["SingletonDigit"]
                singletonsound = singletons[singletonval - 1]
                singletonsound.level = soundlvl  # adjust level
                singletonloc = row["SingletonLoc"]  # get target location
                azimuth, ele = SPACE_ENCODER[singletonloc]  # get coords
                singletonsound_lateralized = lateralize(sound=singletonsound, azimuth=azimuth)  # ITD and ILD
                singletonsound_rendered = externalize(singletonsound_lateralized, azi=azimuth, ele=ele)  # add HRTF
                if singletonsound_rendered.data.shape != trialsound.data.shape:
                    samplediff = singletonsound_rendered.data.shape[0] - trialsound.data.shape[0]
                    singletonsound_rendered.data = singletonsound_rendered[:-samplediff]
                trialsound.data += singletonsound_rendered.data  # add to trial sound
                # digit 2
                digit2val = row["Non-Singleton2Digit"]
                digit2sound = others[digit2val - 1]
                digit2sound.level = soundlvl  # adjust level
                digit2loc = row["Non-Singleton2Loc"]  # get target location
                azimuth, ele = SPACE_ENCODER[digit2loc]  # get coords
                digit2sound_lateralized = lateralize(sound=digit2sound, azimuth=azimuth)  # ITD and ILD
                digit2sound_rendered = externalize(digit2sound_lateralized, azi=azimuth, ele=ele)  # add HRTF
                if digit2sound_rendered.data.shape != trialsound.data.shape:
                    samplediff = digit2sound_rendered.data.shape[0] - trialsound.data.shape[0]
                    digit2sound_rendered.data = digit2sound_rendered[:-samplediff]
                trialsound.data += digit2sound_rendered.data  # add to trial sound

            elif row["SingletonPresent"] == 0:
                print(f"Singleton absent in trial {i}. Computing sound mixture ... ", end="\r")
                # digit 1
                digit1val = row["Non-Singleton1Digit"]
                digit1sound = others[digit1val - 1]
                digit1sound.level = soundlvl  # adjust level
                digit1loc = row["Non-Singleton1Loc"]  # get target location
                azimuth, ele = SPACE_ENCODER[digit1loc]  # get coords
                digit1sound_lateralized = lateralize(sound=digit1sound, azimuth=azimuth)  # ITD and ILD
                digit1sound_rendered = externalize(digit1sound_lateralized, azi=azimuth, ele=ele)  # add HRTF
                if digit1sound_rendered.data.shape != trialsound.data.shape:
                    samplediff = digit1sound_rendered.data.shape[0] - trialsound.data.shape[0]
                    digit1sound_rendered.data = digit1sound_rendered[:-samplediff]
                trialsound.data += digit1sound_rendered.data  # add to trial sound
                # digit 2
                digit2val = row["Non-Singleton2Digit"]
                digit2sound = others[digit2val - 1]
                digit2sound.level = soundlvl  # adjust level
                digit2loc = row["Non-Singleton2Loc"]  # get target location
                azimuth, ele = SPACE_ENCODER[digit2loc]  # get coords
                digit2sound_lateralized = lateralize(sound=digit2sound, azimuth=azimuth)  # ITD and ILD
                digit2sound_rendered = externalize(digit2sound_lateralized, azi=azimuth, ele=ele)  # add HRTF
                if digit2sound_rendered.data.shape != trialsound.data.shape:
                    samplediff = digit2sound_rendered.data.shape[0] - trialsound.data.shape[0]
                    digit2sound_rendered.data = digit2sound_rendered[:-samplediff]
                trialsound.data += digit2sound_rendered.data  # add to trial sound
            print(f"Generated trial sound for trial {i}. Appending to sequence ... ", end="\r")
            sound_sequence.append(trialsound.ramp())  # ramp the sound file to avoid clipping
        for idx, sound in enumerate(sound_sequence):
            sound.write(filename=f"{filename}/s_{idx}.wav")

    print("DONE", end="\r", flush=True)


if __name__ == '__main__':
    # load settings
    settings_path = "WP1/config.yaml"
    with open(settings_path) as file:
        settings = yaml.safe_load(file)

    df = precompute_sequence(sub_id, settings)

