import pandas as pd
import numpy as np
import yaml
import slab
from SPACEPRIME.encoding import SPACE_ENCODER
from utils.signal_processing import spatialize, snr_sound_mixture_two_ears
from utils.utils import get_input_from_dict
from utils import set_logging_level
from SPACEPRIME.trial_sequence_pygad import (make_pygad_trial_sequence, insert_singleton_present_trials,
                                             get_element_indices, print_final_traits)
import os
import seaborn as sns
import matplotlib.pyplot as plt
import logging


# info = get_input_from_dict({"subject_id": 99})

# load settings
settings_path = "SPACEPRIME/config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)

# TODO: debug precompute_sequence()
# temporary
subject_id = 999
logging_level = "INFO"
compute_snr = True


def precompute_sequence(subject_id, settings, logging_level="INFO", compute_snr=True):
    import time
    # log print statements
    logging.basicConfig(filename=settings["filepaths"]["sequences"]+"/logs"+f"/sub-{subject_id}_trial_sequence_log.txt",
                        level=logging_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')  # Customize the timestamp format
    # determine start of function
    start = time.time() / 60
    if compute_snr:
        snr_container = dict(snr_left=[], snr_right=[], signal_loc=[])
    # List all entries (files and directories) in the directory
    for s in os.listdir(settings["filepaths"]["sequences"]):
        if str(subject_id) in s:
            if os.listdir(os.path.join(settings["filepaths"]["sequences"], s)):
                raise FileExistsError(f"Sequence directory for sub-{subject_id} has been created and is not empty! "
                                      f"Please check your sequence directory.")
    # determine how many trials
    n_trials = settings["session"]["n_trials"]
    # load conditions file
    df = pd.read_excel(f"SPACEPRIME/all_combinations_{settings['session']['n_locations']}"
                       f"_loudspeakers_{settings['session']['n_digits']}_digits.xlsx")
    # retrieve sound level to adjust sounds to
    soundlvl = settings["session"]["level"]
    n_blocks = settings["session"]["n_blocks"]
    # iterate over block
    for block in range(n_blocks):
        logging.info(f"Processing block {block}")
        dirname = f"SPACEPRIME/sequences/sub-{subject_id}_block_{block}"
        try:
            os.mkdir(dirname)
        except FileExistsError:
            raise FileExistsError(f"Directory {dirname} already exists")
        sequence, sequence_labels, fitness = make_pygad_trial_sequence(
            fig_path=settings["filepaths"]["sequences"] + "/logs" + f"/sub-{subject_id}_sequence_fitness.png",
            num_trials=n_trials,
            conditions=settings["trial_sequence"]["conditions"],
            prop_c=settings["trial_sequence"]["prop_c"],
            prop_np=settings["trial_sequence"]["prop_np"],
            prop_pp=settings["trial_sequence"]["prop_pp"],
            rule_violation_factor=settings["trial_sequence"]["rule_violation_factor"],
            num_generations=settings["trial_sequence"]["num_generations"],
            num_parents_mating=settings["trial_sequence"]["num_parents_mating"],
            sol_per_pop=settings["trial_sequence"]["sol_per_pop"],
            keep_parents=settings["trial_sequence"]["keep_parents"],
            mutation_percent_genes=settings["trial_sequence"]["mutation_percent_genes"]
        )
        sequence_final = insert_singleton_present_trials(sequence_labels,
                                                         fig_path=settings["filepaths"]["sequences"] + "/logs" +
                                                                  f"/sub-{subject_id}_sequence_hist_sp_trials.png")

        c_indices = get_element_indices(sequence_final, element="C")
        distances_c = np.diff(c_indices)

        # plot the stuff
        sns.histplot(x=distances_c)
        plt.title("Histogram of distances between C trials")
        plt.savefig(
            settings["filepaths"]["sequences"] + "/logs" + f"/sub-{subject_id}_sequence_hist_control_trials.png")
        plt.close()

        # instantiate final trial sequence as placeholder
        trial_sequence = pd.DataFrame()
        # Keep track of the previous trial's values
        prev_target_digit = None
        prev_singleton_digit = None
        prev_target_loc = None
        prev_singleton_loc = None
        # iterate over sequence
        for i, element in enumerate(sequence_final):
            if i > 0:
                previous_element = sequence_final[i - 1]
            else:
                previous_element = None
            while True:  # Loop until a valid trial is found
                select_singleton_present = True if "SP" in element else False
                sample = df[df["SingletonPresent"] == select_singleton_present].sample()
                # set previous singleton loc and digit to None when previous trial was SA and current trial is SA too
                if i > 0:
                    if "SP" not in element and "SP" not in previous_element:
                        prev_singleton_loc = None
                        prev_singleton_digit = None
                # the following are the conditions of negative, no, and positive priming
                if "C" in element:
                    if (
                            sample["TargetDigit"].values[0] != prev_target_digit
                            and sample["SingletonDigit"].values[0] != prev_singleton_digit
                            and sample["TargetLoc"].values[0] != prev_target_loc
                            and sample["SingletonLoc"].values[0] != prev_singleton_loc
                    ):
                        sample["Priming"] = 0
                        break
                if "NP" in element:
                    # NP trial: Target becomes the previous Singleton
                    if (
                            sample["TargetDigit"].values[0] == prev_singleton_digit
                            and sample["TargetLoc"].values[0] == prev_singleton_loc
                    ):
                        sample["Priming"] = -1
                        break
                elif "PP" in element:
                    # PP trial: Target remains the same
                    if (
                            sample["TargetDigit"].values[0] == prev_target_digit
                            and sample["TargetLoc"].values[0] == prev_target_loc
                    ):
                        sample["Priming"] = 1
                        break

            logging.debug(f"Found suited condition matching {element}.")

            # Update the previous trial's values
            prev_target_digit = sample["TargetDigit"].values[0]
            prev_singleton_digit = sample["SingletonDigit"].values[0]
            prev_target_loc = sample["TargetLoc"].values[0]
            prev_singleton_loc = sample["SingletonLoc"].values[0]

            df_final = trial_sequence._append(sample)
            logging.debug(
                f"Appended sample to trial sequence. Length of current trial sequence: {df_final.__len__()}")

        df_final.reset_index(drop=True, inplace=True)
        print_final_traits(df_final)
        df_final["ITI-Jitter"] = generate_balanced_jitter(df_final, iti=settings["session"]["iti"])
        df_final["ITI-Jitter"] = round(df_final["ITI-Jitter"], 3)
        file_name = f"SPACEPRIME/sequences/sub-{subject_id}_block_{block}.xlsx"
        df_final.to_excel(file_name, index=False)  # Save as CSV, excluding the row index
        logging.info(f"Precomputing trial sounds for subject {subject_id}, block {block} ... ")
        sound_sequence = []

        # load sounds
        singletons = [slab.Sound.read(f"stimuli/distractors_{settings['session']['distractor_type']}/{x}")
                      for x in os.listdir(f"stimuli/distractors_{settings['session']['distractor_type']}")]
        targets = [slab.Sound.read(f"stimuli/targets/{x}") for x in os.listdir(f"../stimuli/targets")]
        others = [slab.Sound.read(f"stimuli/digits_all_250ms/{x}") for x in os.listdir(f"../stimuli/digits_all_250ms")]

        # set equal level
        for s, t, o in zip(singletons, targets, others):
            s.level = soundlvl
            t.level = soundlvl
            o.level = soundlvl

        # binauralize
        singletons = [slab.Binaural(data=x) for x in singletons]
        targets = [slab.Binaural(data=x) for x in targets]
        others = [slab.Binaural(data=x) for x in others]

        for i, row in df_final.iterrows():
            logging.debug(f"Precompute trialsound for trial {i}, block {block} ... ")
            # make trial sound container
            trialsound = slab.Binaural.silence(duration=settings["session"]["stimulus_duration"],
                                               samplerate=settings["session"]["samplerate"])
            # get targets
            targetval = int(row["TargetDigit"])
            targetsound = targets[targetval - 1]
            targetsound.level = soundlvl  # adjust level
            targetloc = row["TargetLoc"]  # get target location
            azimuth, ele = SPACE_ENCODER[targetloc]  # get coords
            # targetsound_lateralized = lateralize(sound=targetsound, azimuth=azimuth)  # ITD and ILD
            targetsound_rendered = spatialize(targetsound, azi=azimuth, ele=ele)  # add HRTF
            if targetsound_rendered.data.shape != trialsound.data.shape:
                samplediff = targetsound_rendered.data.shape[0] - trialsound.data.shape[0]
                targetsound_rendered.data = targetsound_rendered[:-samplediff]
            trialsound.data += targetsound_rendered.data  # add to trial sound

            if row["SingletonPresent"] == 1:
                logging.debug(f"Singleton present in trial {i}. Computing sound mixture ... ")
                # singleton
                singletonval = int(row["SingletonDigit"])
                singletonsound = singletons[singletonval - 1]
                singletonsound.level = soundlvl  # adjust level
                singletonloc = row["SingletonLoc"]  # get target location
                azimuth, ele = SPACE_ENCODER[singletonloc]  # get coords
                # singletonsound_lateralized = lateralize(sound=singletonsound, azimuth=azimuth)  # ITD and ILD
                singletonsound_rendered = spatialize(singletonsound, azi=azimuth, ele=ele)  # add HRTF
                if singletonsound_rendered.data.shape != trialsound.data.shape:
                    samplediff = singletonsound_rendered.data.shape[0] - trialsound.data.shape[0]
                    singletonsound_rendered.data = singletonsound_rendered[:-samplediff]
                trialsound.data += singletonsound_rendered.data  # add to trial sound
                # digit 2
                digit2val = int(row["Non-Singleton2Digit"])
                digit2sound = others[digit2val - 1]
                digit2sound.level = soundlvl  # adjust level
                digit2loc = row["Non-Singleton2Loc"]  # get target location
                azimuth, ele = SPACE_ENCODER[digit2loc]  # get coords
                # digit2sound_lateralized = lateralize(sound=digit2sound, azimuth=azimuth)  # ITD and ILD
                digit2sound_rendered = spatialize(digit2sound, azi=azimuth, ele=ele)  # add HRTF
                if digit2sound_rendered.data.shape != trialsound.data.shape:
                    samplediff = digit2sound_rendered.data.shape[0] - trialsound.data.shape[0]
                    digit2sound_rendered.data = digit2sound_rendered[:-samplediff]
                trialsound.data += digit2sound_rendered.data  # add to trial sound

            elif row["SingletonPresent"] == 0:
                logging.debug(f"Singleton absent in trial {i}. Computing sound mixture ... ")
                # digit 1
                digit1val = int(row["Non-Singleton1Digit"])
                digit1sound = others[digit1val - 1]
                digit1sound.level = soundlvl  # adjust level
                digit1loc = row["Non-Singleton1Loc"]  # get target location
                azimuth, ele = SPACE_ENCODER[digit1loc]  # get coords
                # digit1sound_lateralized = lateralize(sound=digit1sound, azimuth=azimuth)  # ITD and ILD
                digit1sound_rendered = spatialize(digit1sound, azi=azimuth, ele=ele)  # add HRTF
                if digit1sound_rendered.data.shape != trialsound.data.shape:
                    samplediff = digit1sound_rendered.data.shape[0] - trialsound.data.shape[0]
                    digit1sound_rendered.data = digit1sound_rendered[:-samplediff]
                trialsound.data += digit1sound_rendered.data  # add to trial sound
                # digit 2
                digit2val = int(row["Non-Singleton2Digit"])
                digit2sound = others[digit2val - 1]
                digit2sound.level = soundlvl  # adjust level
                digit2loc = row["Non-Singleton2Loc"]  # get target location
                azimuth, ele = SPACE_ENCODER[digit2loc]  # get coords
                # digit2sound_lateralized = lateralize(sound=digit2sound, azimuth=azimuth)  # ITD and ILD
                digit2sound_rendered = spatialize(digit2sound, azi=azimuth, ele=ele)  # add HRTF
                if digit2sound_rendered.data.shape != trialsound.data.shape:
                    samplediff = digit2sound_rendered.data.shape[0] - trialsound.data.shape[0]
                    digit2sound_rendered.data = digit2sound_rendered[:-samplediff]
                trialsound.data += digit2sound_rendered.data  # add to trial sound
            # subtract level difference from final sound file
            # trialsound.level = trialsound.level - (trialsound.level - soundlvl)
            logging.debug(f"Generated trial sound for trial {i}. Appending to sequence ... ")
            sound_sequence.append(trialsound.ramp())  # ramp the sound file to avoid clipping
            # compute snr
            if compute_snr:
                signal = targetsound_rendered
                if row["SingletonPresent"] == 0:
                    noise = digit1sound_rendered + digit2sound_rendered
                elif row["SingletonPresent"] == 1:
                    noise = singletonsound_rendered + digit2sound_rendered
                snr_left, snr_right = snr_sound_mixture_two_ears(signal, noise)
                snr_container["snr_left"].append(snr_left[0])
                snr_container["snr_right"].append(snr_right[0])
                azimuth, _ = SPACE_ENCODER[targetloc]
                snr_container["signal_loc"].append(azimuth)

        if compute_snr:
            df = pd.DataFrame.from_dict(snr_container)
            file_name_snr = f"SPACEPRIME/sequences/sub-{subject_id}_block_{block}_snr.xlsx"
            df.to_excel(file_name_snr, index=False)
        # write sound to .wav
        for idx, sound in enumerate(sound_sequence):
            sound.write(filename=f"{dirname}/s_{idx}.wav", normalise=False)  # normalise param is broken ...
    stop = time.time() / 60
    logging.info("DONE")
    logging.info(f"Total time for script running: {stop - start:.2f} minutes")


def generate_balanced_jitter(df, iti, tolerance=0.001):
    df_0 = df[df['SingletonPresent'] == 0]
    df_1 = df[df['SingletonPresent'] == 1]

    while True:
        jitter_0 = np.random.uniform(iti-iti*0.25, iti+iti*0.25, size=len(df_0))
        jitter_1 = np.random.uniform(iti-iti*0.25, iti+iti*0.25, size=len(df_1))

        mean_jitter_0 = np.mean(jitter_0)
        mean_jitter_1 = np.mean(jitter_1)

        if abs(mean_jitter_0 - mean_jitter_1) < tolerance:
            break

    return pd.Series(np.concatenate([jitter_0, jitter_1]), index=df.index)


if __name__ == "__main__":
    precompute_sequence(subject_id=subject_id, settings=settings)
