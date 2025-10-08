import pandas as pd
import numpy as np
import yaml
import slab
from encoding import SPACE_ENCODER
from utils.signal_processing import spatialize, snr_sound_mixture_two_ears
from utils.utils import get_input_from_dict, generate_balanced_jitter
from trial_sequence_pygad import (make_pygad_trial_sequence, insert_singleton_present_trials,
                                  get_element_indices, print_final_traits)
import os
import seaborn as sns
import matplotlib.pyplot as plt
import logging
import time

info = get_input_from_dict({"subject_id": 99, "block": 0})

# load settings
settings_path = "config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)


def precompute_sequence(subject_id, block, settings, logging_level="INFO", compute_snr=False):
    # --- FIX: Ensure subject_id is an integer ---
    try:
        subject_id = int(subject_id)
    except (ValueError, TypeError):
        logging.error(f"Invalid subject_id: {subject_id}. It must be convertible to an integer.")
        raise

    # get relevant params from settings
    samplerate = settings["session"]["samplerate"]
    freefield = settings["mode"]['freefield']
    # log print statements
    logging.basicConfig(
        filename=settings["filepaths"]["sequences"] + "/logs" + f"/sci-{subject_id}_trial_sequence_log.txt",
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
            if os.path.isdir(os.path.join(settings["filepaths"]["sequences"], s)) and \
                    os.listdir(os.path.join(settings["filepaths"]["sequences"], s)):
                raise FileExistsError(f"Sequence directory for sci-{subject_id} has been created and is not empty! "
                                      f"Please check your sequence directory.")
    # determine how many trials
    n_trials = settings["session"]["n_trials"]
    # load conditions file
    df = pd.read_csv(f"all_combinations_{settings['session']['n_locations']}"
                     f"_loudspeakers_{settings['session']['n_digits']}_digits.csv")
    # retrieve sound level to adjust sounds to
    soundlvl = settings["session"]["level"]
    n_blocks = settings["session"]["n_blocks"]
    # midpoint = n_blocks // 2  # pitch everything but singletons after 50 % of blocks
    # load sounds
    singletons = [slab.Sound.read(f"stimuli/distractors_{settings['session']['distractor_type']}/{x}")
                  for x in os.listdir(f"stimuli/distractors_{settings['session']['distractor_type']}")]

    # --- SUGGESTION: Corrected path typo ---
    targets = [slab.Sound.read(f"stimuli/targets_low_30_Hz/{x}") for x in
               os.listdir(f"stimuli/targets_low_30_Hz")]  # Corrected 'hz' to 'Hz'

    others = [slab.Sound.read(f"stimuli/digits_all_250ms/{x}") for x in
              os.listdir(f"stimuli/digits_all_250ms")]

    # set equal level --> this sets the RMS value of all sounds to an equal level :)
    for s, t, o in zip(singletons, targets, others):
        s.level = soundlvl
        t.level = soundlvl
        o.level = soundlvl

    # binauralize if not freefield mode
    if not freefield:
        singletons = [slab.Binaural(data=x) for x in singletons]
        targets = [slab.Binaural(data=x) for x in targets]
        others = [slab.Binaural(data=x) for x in others]

    # --- START: Added for biased singleton location ---
    is_even_subject = subject_id % 2 == 0
    n_locations = settings["session"]["n_locations"]
    all_locs = list(range(1, n_locations + 1))
    # --- END: Added for biased singleton location ---

    # iterate over block
    for block in range(block, n_blocks):
        print(f"Running block {block}")
        """if block >= midpoint:
            # really confusing but this should do the trick
            if subject_id_is_even:
                targets = targets_high
                others = singletons_copy
                singletons = others_copy
            if not subject_id_is_even:
                targets = targets_low
                singletons = singletons_copy
                others = others_copy"""
        logging.info(f"Processing block {block}")
        dirname = f"sequences/sci-{subject_id}_block_{block}"
        try:
            os.mkdir(dirname)
        except FileExistsError:
            logging.warning(f"Directory {dirname} already exists! Moving on ... ")
        sequence, sequence_labels, fitness = make_pygad_trial_sequence(
            fig_path=settings["filepaths"][
                         "sequences"] + "/logs" + f"/sci-{subject_id}_block-{block}_sequence_fitness.png",
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
                                                                  f"/sci-{subject_id}_sequence_block-{block}_hist_sp_trials.png")

        c_indices = get_element_indices(sequence_final, element="C")
        distances_c = np.diff(c_indices)
        # plot the stuff
        sns.histplot(x=distances_c)
        plt.title("Histogram of distances between C trials")
        plt.savefig(
            settings["filepaths"]["sequences"] + "/logs" + f"/sci-{subject_id}_sequence_hist_block{block}_"
                                                           f"diff_control_trials.png")
        plt.close()

        # instantiate final trial sequence as placeholder
        trial_sequence = pd.DataFrame()
        # Keep track of the previous trial's values
        prev_target_digit = None
        prev_singleton_digit = None
        prev_target_loc = None
        prev_singleton_loc = None

        # --- START: REPLACEMENT FOR THE TRIAL INSTANTIATION LOOP ---
        for i, element in enumerate(sequence_final):
            # --- Emergency Safeguards (from original code) ---
            if i == 0 and "C" not in element:
                logging.warning(f"First trial is not a control trial. Fixing. Old: {element}, New: C_SP")
                element = "C_SP"

            if i > 0:
                previous_element = sequence_final[i - 1]
                if "NP" in element and "NP" in previous_element:
                    logging.warning(f"Fixing consecutive NP trial at index {i}. Changing to Control.")
                    element = element.replace("NP", "C")

            # 1. Define the pool of candidates for this trial
            select_singleton_present = "SP" in element
            candidate_pool = df[df["SingletonPresent"] == select_singleton_present].copy()

            # 2. Apply trial-to-trial constraint filtering
            if i > 0:  # No constraints for the first trial
                if "C" in element:
                    # EXCLUDE all known priming/repetition relationships
                    # Note: if prev_singleton_digit is None (from an SA trial), these comparisons correctly yield False.
                    pp_mask = (candidate_pool["TargetDigit"] == prev_target_digit) & (
                            candidate_pool["TargetLoc"] == prev_target_loc)
                    np_mask = (candidate_pool["TargetDigit"] == prev_singleton_digit) & (
                            candidate_pool["TargetLoc"] == prev_singleton_loc)
                    ar_mask = (candidate_pool["SingletonDigit"] == prev_target_digit) & (
                            candidate_pool["SingletonLoc"] == prev_target_loc)
                    ir_mask = (candidate_pool["SingletonDigit"] == prev_singleton_digit) & (
                            candidate_pool["SingletonLoc"] == prev_singleton_loc)

                    # Filter out any trial that matches any of these repetition conditions
                    candidate_pool = candidate_pool[~(pp_mask | np_mask | ar_mask | ir_mask)]

                elif "NP" in element:
                    # REQUIRE the Negative Priming relationship
                    if prev_singleton_digit is None:
                        raise ValueError(
                            f"Impossible sequence: NP trial at index {i} follows a Singleton-Absent trial.")

                    inclusion_mask = (candidate_pool["TargetDigit"] == prev_singleton_digit) & (
                            candidate_pool["TargetLoc"] == prev_singleton_loc)
                    candidate_pool = candidate_pool[inclusion_mask]

                elif "PP" in element:
                    # REQUIRE the Positive Priming relationship
                    inclusion_mask = (candidate_pool["TargetDigit"] == prev_target_digit) & (
                            candidate_pool["TargetLoc"] == prev_target_loc)
                    candidate_pool = candidate_pool[inclusion_mask]

            # 3. Apply biased singleton location logic (if applicable and possible)
            if select_singleton_present and not candidate_pool.empty:
                biased_loc = 1 if is_even_subject else 3
                if biased_loc in all_locs:
                    other_locs = [loc for loc in all_locs if loc != biased_loc]

                    # Decide if we pick the biased location (80% chance)
                    if np.random.rand() < 0.70:
                        high_prob_trials = candidate_pool[candidate_pool["SingletonLoc"] == biased_loc]
                        if not high_prob_trials.empty:
                            candidate_pool = high_prob_trials
                    else:
                        low_prob_trials = candidate_pool[candidate_pool["SingletonLoc"].isin(other_locs)]
                        if not low_prob_trials.empty:
                            candidate_pool = low_prob_trials

            # 4. Final sampling and error handling
            if candidate_pool.empty:
                logging.error(f"Could not find a valid trial for element '{element}' at index {i}. "
                              f"Previous trial had: T_digit={prev_target_digit}, T_loc={prev_target_loc}, "
                              f"S_digit={prev_singleton_digit}, S_loc={prev_singleton_loc}. "
                              f"This indicates the GA-generated sequence is impossible to fulfill.")
                raise ValueError(f"Impossible sequence generated. Could not find trial for '{element}' at index {i}.")

            sample = candidate_pool.sample(1).copy()  # Use .copy() to avoid SettingWithCopyWarning

            # 5. Add metadata and update state
            # Set Priming label
            if "C" in element:
                sample["Priming"] = 0
            elif "NP" in element:
                sample["Priming"] = -1
            elif "PP" in element:
                sample["Priming"] = 1

            # Add distractor probability column
            if not select_singleton_present:
                sample["DistractorProb"] = "distractor-absent"
            else:
                biased_loc = 1 if is_even_subject else 3
                actual_singleton_loc = sample["SingletonLoc"].values[0]
                if actual_singleton_loc == biased_loc:
                    sample["DistractorProb"] = "high-probability"
                else:
                    sample["DistractorProb"] = "low-probability"

            # Update the previous trial's values for the next iteration
            prev_target_digit = sample["TargetDigit"].values[0]
            prev_singleton_digit = sample["SingletonDigit"].values[0] if select_singleton_present else None
            prev_target_loc = sample["TargetLoc"].values[0]
            prev_singleton_loc = sample["SingletonLoc"].values[0] if select_singleton_present else None

            trial_sequence = pd.concat([trial_sequence, sample], ignore_index=True)
            logging.debug(f"Found and appended trial for {element}. Sequence length: {len(trial_sequence)}")
        # --- END: REPLACEMENT LOOP ---

        trial_sequence.reset_index(drop=True, inplace=True)
        print_final_traits(trial_sequence)
        trial_sequence["ITI-Jitter"] = generate_balanced_jitter(trial_sequence, iti=settings["session"]["iti"])
        trial_sequence["ITI-Jitter"] = round(trial_sequence["ITI-Jitter"], 3)
        file_name = f"sequences/sci-{subject_id}_block_{block}.csv"
        trial_sequence.to_csv(file_name, index=False)  # Save as CSV, excluding the row index
        logging.info(f"Precomputing trial sounds for subject {subject_id}, block {block} ... ")

        sound_sequence = []  # sound sequence placeholder
        for i, row in trial_sequence.iterrows():
            logging.debug(f"Precompute trialsound for trial {i}, block {block} ... ")
            # make trial sound container
            if not freefield:
                trialsound = slab.Binaural.silence(duration=settings["session"]["stimulus_duration"],
                                                   samplerate=samplerate)
            elif freefield:
                trialsound = np.array([np.zeros(int(samplerate * settings["session"]["stimulus_duration"])),
                                       np.zeros(int(samplerate * settings["session"]["stimulus_duration"])),
                                       np.zeros(int(samplerate * settings["session"]["stimulus_duration"]))])
            # get targets
            targetval = int(row["TargetDigit"])
            targetsound = targets[targetval - 1]
            targetsound.level = soundlvl  # adjust level
            targetloc = row["TargetLoc"]  # get target location
            if not freefield:
                azimuth, ele = SPACE_ENCODER[targetloc]  # get coords
                targetsound_rendered = spatialize(targetsound, azi=azimuth, ele=ele)  # add HRTF
                if targetsound_rendered.n_samples != trialsound.n_samples:
                    targetsound_rendered = targetsound_rendered.resize(trialsound.n_samples)
                trialsound.data += targetsound_rendered.data  # add to trial sound
            if freefield:
                trialsound[int(targetloc - 1)] = targetsound.data[:, 0]
            if row["SingletonPresent"] == 1:
                logging.debug(f"Singleton present in trial {i}. Computing sound mixture ... ")
                # singleton
                singletonval = int(row["SingletonDigit"])
                singletonsound = singletons[singletonval - 1]
                singletonsound.level = soundlvl  # adjust level
                singletonloc = row["SingletonLoc"]  # get target location
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[singletonloc]  # get coords
                    singletonsound_rendered = spatialize(singletonsound, azi=azimuth, ele=ele)  # add HRTF
                    if singletonsound_rendered.n_samples != trialsound.n_samples:
                        singletonsound_rendered = singletonsound_rendered.resize(trialsound.n_samples)
                    trialsound.data += singletonsound_rendered.data  # add to trial sound
                if freefield:
                    trialsound[int(singletonloc - 1)] = singletonsound.data[:, 0]

                # digit 2
                digit2val = int(row["Non-Singleton2Digit"])
                digit2sound = others[digit2val - 1]
                digit2sound.level = soundlvl  # adjust level
                digit2loc = row["Non-Singleton2Loc"]  # get target location
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[digit2loc]  # get coords
                    digit2sound_rendered = spatialize(digit2sound, azi=azimuth, ele=ele)  # add HRTF
                    if digit2sound_rendered.n_samples != trialsound.n_samples:
                        digit2sound_rendered = digit2sound_rendered.resize(trialsound.n_samples)
                    trialsound.data += digit2sound_rendered.data  # add to trial sound
                if freefield:
                    trialsound[int(digit2loc - 1)] = digit2sound.data[:, 0]

            elif row["SingletonPresent"] == 0:
                logging.debug(f"Singleton absent in trial {i}. Computing sound mixture ... ")
                # digit 1
                digit1val = int(row["Non-Singleton1Digit"])
                digit1sound = others[digit1val - 1]
                digit1sound.level = soundlvl  # adjust level
                digit1loc = row["Non-Singleton1Loc"]  # get target location
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[digit1loc]  # get coords
                    digit1sound_rendered = spatialize(digit1sound, azi=azimuth, ele=ele)  # add HRTF
                    if digit1sound_rendered.n_samples != trialsound.n_samples:
                        digit1sound_rendered = digit1sound_rendered.resize(trialsound.n_samples)
                    trialsound.data += digit1sound_rendered.data  # add to trial sound
                if freefield:
                    trialsound[int(digit1loc - 1)] = digit1sound.data[:, 0]

                # digit 2
                digit2val = int(row["Non-Singleton2Digit"])
                digit2sound = others[digit2val - 1]
                digit2sound.level = soundlvl  # adjust level
                digit2loc = row["Non-Singleton2Loc"]  # get target location
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[digit2loc]  # get coords
                    digit2sound_rendered = spatialize(digit2sound, azi=azimuth, ele=ele)  # add HRTF
                    if digit2sound_rendered.n_samples != trialsound.n_samples:
                        digit2sound_rendered = digit2sound_rendered.resize(trialsound.n_samples)
                    trialsound.data += digit2sound_rendered.data  # add to trial sound
                if freefield:
                    trialsound[int(digit2loc - 1)] = digit2sound.data[:, 0]
            trialsound_slab = slab.Sound(trialsound, samplerate=samplerate)
            logging.debug(f"Generated trial sound for trial {i}. Appending to sequence ... ")
            sound_sequence.append(trialsound_slab.ramp())  # ramp the sound file to avoid clipping
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
                df_snr = pd.DataFrame.from_dict(snr_container)
                file_name_snr = f"sequences/sci-{subject_id}_block_{block}_snr.csv"
                df_snr.to_csv(file_name_snr, index=False)

        # write sound to .wav
        for idx, sound in enumerate(sound_sequence):
            print(f"Writing sound {idx}")
            sound.write(filename=f"{dirname}/s_{idx}.wav", normalise=False)

    stop = time.time() / 60
    logging.info("DONE")
    logging.info(f"Total script running time: {stop - start:.2f} minutes")


precompute_sequence(subject_id=info["subject_id"], block=info["block"], settings=settings)