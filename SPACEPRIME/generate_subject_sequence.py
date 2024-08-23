import pandas as pd
import numpy as np
import yaml
import slab
from SPACEPRIME.encoding import SPACE_ENCODER
from utils.signal_processing import spatialize, snr_sound_mixture_two_ears
from utils.utils import get_input_from_dict
import sys
import os


# NEW APPROACH: put a control trial after every priming trial, acquire 50% C and 25% PP/NP trials,
# 50% Singleton present, 1800 total trials.
# info = get_input_from_dict({"subject_id": 99})


def precompute_sequence(subject_id, settings, compute_snr=True):
    import time
    # determine start of function
    start = time.time() / 60
    if compute_snr:
        snr_container = dict(snr_left=[], snr_right=[], signal_loc=[])
    # subject_id = '0' + str(subject_id) if subject_id < 10 else str(subject_id)
    if any(str(subject_id) in s for s in os.listdir("SPACEPRIME/sequences")):
        raise FileExistsError(f"Sequences for sub-{subject_id} has already been created! "
                              f"Please check your sequence directory.")
    # determine how many trials
    n_trials = settings["session"]["n_trials"]
    # load conditions file
    df = pd.read_excel(f"SPACEPRIME/all_combinations_{settings['session']['n_locations']}"
                       f"_loudspeakers_{settings['session']['n_digits']}_digits.xlsx")
    # retrieve sound level to adjust sounds to
    soundlvl = settings["session"]["level"]
    # make copy
    df_copy = df.copy()
    n_blocks = settings["session"]["n_blocks"]


if __name__ == "__main__":
    import random
    subject_id = 999
    # load settings
    settings_path = "SPACEPRIME/config.yaml"
    with open(settings_path) as file:
        settings = yaml.safe_load(file)

    # subject_id = '0' + str(subject_id) if subject_id < 10 else str(subject_id)
    if any(str(subject_id) in s for s in os.listdir("SPACEPRIME/sequences")):
        raise FileExistsError(f"Sequences for sub-{subject_id} has already been created! "
                              f"Please check your sequence directory.")
    # load conditions file
    df = pd.read_excel(f"SPACEPRIME/all_combinations_{settings['session']['n_locations']}"
                       f"_loudspeakers_{settings['session']['n_digits']}_digits.xlsx")
    # retrieve sound level to adjust sounds to
    soundlvl = settings["session"]["level"]
    # make copy
    n_blocks = settings["session"]["n_blocks"]
    # determine how many trials
    n_trials = settings["session"]["n_trials"]


    def generate_sequence(n_trials):
        sequence = []
        priming_sequence = ["NP", "PP"]
        sequence.append("C")  # sequence must start with a C
        total_sp_trials = n_trials // 2
        # Ensure every other element is "C"
        for _ in enumerate(range(n_trials//2)):
            sequence.append("C")
            choice = random.choice(priming_sequence)
            sequence.append(choice)
        for i, trial in enumerate(sequence):
            if trial == "NP":  # previous trial must be C trial
                sequence[i-1] = sequence[i-1] + "_SP"
        current_sps_trials = 0
        for count in sequence:
            if "_SP" in count:
                current_sps_trials += 1
        remaining_sp_trials = total_sp_trials - current_sps_trials
        no_sp_trials_idx = [i for i, element in enumerate(sequence) if "_SP" not in element]
        random_samples = random.sample(no_sp_trials_idx, remaining_sp_trials)
        for random_sample in random_samples:
            sequence[random_sample] = sequence[random_sample] + "_SP"
        # sanity check
        sp_count = 0
        np_count = 0
        pp_count = 0
        c_count = 0
        for t in sequence:
            if "SP" in t:
                sp_count += 1
            if "NP" in t:
                np_count += 1
            if "PP" in t:
                pp_count += 1
            if "C" in t:
                c_count += 1
        print(f"SEQUENCE CONTAINS: \n"
              f"Total trials: {n_trials} \n"
              f"Singleton present trials: {sp_count} \n"
              f"Negative priming trials: {np_count} \n"
              f"Positive priming trials: {pp_count} \n"
              f"No priming trials: {c_count}")
        return sequence

    # Generate the sequence
    sequence = generate_sequence(n_trials)

    import matplotlib.pyplot as plt
    plt.ion()

    def get_sp_indices(sequence):
        return [i for i, element in enumerate(sequence) if "SP" in element]

    sp_indices = get_sp_indices(sequence)
    distances = np.diff(sp_indices)
    plt.hist(distances, bins=len(np.unique(distances)), edgecolor='black')  # Adjust bins as needed
    plt.title('Histogram of Distances between SP Elements')
    plt.xlabel('Distance')
    plt.ylabel('Frequency')

    # Display the plot
    # initiate final trial sequence as placeholder
    trial_sequence = pd.DataFrame()
    # Keep track of the previous trial's values
    prev_target_digit = None
    prev_singleton_digit = None
    prev_target_loc = None
    prev_singleton_loc = None
    upcoming_element = None
    # Calculate the desired number of "SingletonPresent" == 1 trials
    target_singleton_present_trials = n_trials // 2
    current_singleton_present_trials = 0
    # iterate over sequence
    for i, element in enumerate(sequence):
        while True:  # Loop until a valid trial is found
            if i < len(sequence) - 1:
                upcoming_element = sequence[i+1]
            else:
                upcoming_element = None
            if upcoming_element == "NP" and element == "C":
                select_singleton_present = 1  # ensure SP prime present in NP trials
            else:
                select_singleton_present = random.choices([1, 0], weights=[0.01, 0.99])[0]
            sample = df[df["SingletonPresent"] == select_singleton_present].sample()
            # the following are the conditions of negative, no, and positive priming
            if element == "C":
                if (
                    sample["TargetDigit"].values[0] != prev_target_digit
                    and sample["SingletonDigit"].values[0] != prev_singleton_digit
                    and sample["TargetLoc"].values[0] != prev_target_loc
                    and sample["SingletonLoc"].values[0] != prev_singleton_loc
                ):
                    sample["Priming"] = 1
                    break
            if element == "NP":
                # NP trial: Target becomes the previous Singleton
                if (
                    sample["TargetDigit"].values[0] == prev_singleton_digit
                    and sample["TargetLoc"].values[0] == prev_singleton_loc
                ):
                    sample["Priming"] = 0
                    break
            elif element == "PP":
                # PP trial: Target remains the same
                if (
                    sample["TargetDigit"].values[0] == prev_target_digit
                    and sample["TargetLoc"].values[0] == prev_target_loc
                ):
                    sample["Priming"] = 2
                    break

        print(f"Found suited condition matching {element}.")
        current_singleton_present_trials += 1 if select_singleton_present else 0
        print(f"Current singleton present trials: {current_singleton_present_trials}.")

        # Update the previous trial's values
        prev_target_digit = sample["TargetDigit"].values[0]
        prev_singleton_digit = sample["SingletonDigit"].values[0]
        prev_target_loc = sample["TargetLoc"].values[0]
        prev_singleton_loc = sample["SingletonLoc"].values[0]

        trial_sequence = trial_sequence._append(sample)
        print(f"Appended sample to trial sequence. Length of current trial sequence: {trial_sequence.__len__()}")

trial_sequence.reset_index(drop=True, inplace=True)

singleton_indices = trial_sequence[trial_sequence['SingletonPresent'] == 1].index
# Calculate the differences between consecutive indices to get the number of rows until a 1 appears
distances = singleton_indices.to_series().diff().dropna().astype(int)
# Plot a histogram of the distances
plt.hist(distances, bins=10, edgecolor='black')  # Adjust bins as needed
plt.xlabel('Number of Rows until SingletonPresent == 1')
plt.ylabel('Frequency')
plt.title('Distances between SingletonPresent == 1')
