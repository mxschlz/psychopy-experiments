import pandas as pd
import numpy as np
import yaml
import slab
from SPACECUE.encoding import SPACE_ENCODER
from utils.signal_processing import spatialize, snr_sound_mixture_two_ears
from utils.utils import get_input_from_dict, generate_balanced_jitter
from SPACECUE.trial_sequence_pygad import (make_pygad_trial_sequence, insert_singleton_present_trials,
                                           get_element_indices, print_final_traits)
import os
import seaborn as sns
import matplotlib.pyplot as plt
import logging
import time
from copy import deepcopy


#os.chdir("C:/Users/Max/PycharmProjects/psychopy-experiments/SPACECUE")

info = get_input_from_dict({"subject_id": 99, "block": 0})

# load settings
settings_path = "config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)


def _check_max_consecutive_items(data_list: list, item_to_check: any, max_allowed: int) -> bool:
    """
    Checks if an item appears consecutively more than max_allowed times in a list.
    (Implementation as provided previously)
    """
    if not data_list or max_allowed <= 0:
        if max_allowed <= 0 and item_to_check in data_list:
            return False
        return True
    current_consecutive = 0
    for item in data_list:
        if item == item_to_check:
            current_consecutive += 1
            if current_consecutive > max_allowed:
                return False
        else:
            current_consecutive = 0
    return True


def insert_pseudo_randomized_cues(df: pd.DataFrame,
                                  block_num: int,
                                  subject_is_even: bool,
                                  prop_informative: float = 0.8, # This setting will now be used for both strategies
                                  max_consecutive_block_cues: int = 5,
                                  max_consecutive_trial_cues: int = 5) -> pd.DataFrame:
    """
    Inserts a column "CueInstruction" into the DataFrame.
    Logic depends on whether the subject_id is even (trial-wise cueing) or odd (block-wise cueing).

    Args:
        df (pd.DataFrame): The trial sequence DataFrame for the current block.
        block_num (int): The current block number.
        subject_is_even (bool): True if the subject ID is even (trial-wise cueing),
                                False if odd (block-wise cueing).
        prop_informative (float): Proportion of trials for informative cues (target/distractor).
                                  Used for both block-wise and trial-wise modes.
        max_consecutive_block_cues (int): Max consecutive informative cues in block-wise mode.
        max_consecutive_trial_cues (int): Max consecutive same-type cues (target/distractor/neutral)
                                          in trial-wise mode.

    Returns:
        pd.DataFrame: The DataFrame with the added "CueInstruction" column.
    """
    if 'SingletonPresent' not in df.columns and not subject_is_even:
        logging.error("DataFrame must contain 'SingletonPresent' column for block-wise cueing strategy.")
        df["CueInstruction"] = "error_missing_singleton_info"
        return df

    df["CueInstruction"] = pd.NA

    cue_target_label = "cue_target_location"
    cue_distractor_label = "cue_distractor_location"
    uninformative_cue_label = "cue_neutral"

    if subject_is_even:
        # --- TRIAL-WISE CUEING LOGIC (Even Subjects) ---
        logging.info(f"Block {block_num}: Applying TRIAL-WISE cueing strategy (Even Subject).")
        n_total_trials = len(df)

        if n_total_trials == 0:
            logging.warning(f"Block {block_num} (Trial-wise): DataFrame is empty. No cues to assign.")
            return df

        n_informative_total = int(round(prop_informative * n_total_trials))
        n_uninformative_total = n_total_trials - n_informative_total
        n_target_informative = n_informative_total // 2
        n_distractor_informative = n_informative_total - n_target_informative

        logging.info(f"Block {block_num} (Trial-wise): Total trials: {n_total_trials}. "
                     f"Prop informative: {prop_informative*100:.0f}%. "
                     f"Assigning {n_informative_total} informative ({n_target_informative} target, {n_distractor_informative} distractor) "
                     f"and {n_uninformative_total} neutral ('{uninformative_cue_label}'). "
                     f"Max consecutive ANY type: {max_consecutive_trial_cues}.")

        cues_for_block_prototype = ([cue_target_label] * n_target_informative +
                                    [cue_distractor_label] * n_distractor_informative +
                                    [uninformative_cue_label] * n_uninformative_total)
        cues_for_block_list = list(cues_for_block_prototype)

        if n_total_trials > 0:
            max_shuffling_attempts = 500
            found_valid_sequence = False

            if (n_target_informative > max_consecutive_trial_cues or
                n_distractor_informative > max_consecutive_trial_cues or
                n_uninformative_total > max_consecutive_trial_cues):
                min_other_needed_target = (n_target_informative - 1) // max_consecutive_trial_cues if n_target_informative > 0 else 0
                min_other_needed_distractor = (n_distractor_informative - 1) // max_consecutive_trial_cues if n_distractor_informative > 0 else 0
                min_other_needed_neutral = (n_uninformative_total - 1) // max_consecutive_trial_cues if n_uninformative_total > 0 else 0
                total_others_for_target = n_distractor_informative + n_uninformative_total
                total_others_for_distractor = n_target_informative + n_uninformative_total
                total_others_for_neutral = n_target_informative + n_distractor_informative

                if (n_target_informative > 0 and total_others_for_target < min_other_needed_target) or \
                   (n_distractor_informative > 0 and total_others_for_distractor < min_other_needed_distractor) or \
                   (n_uninformative_total > 0 and total_others_for_neutral < min_other_needed_neutral):
                     logging.warning(
                         f"Block {block_num} (Trial-wise): Potentially not enough other cue types "
                         f"to strictly enforce max_consecutive_trial_cues={max_consecutive_trial_cues} "
                         f"for all cue types. Will attempt to shuffle but constraint might not be met."
                     )

            for attempt in range(max_shuffling_attempts):
                np.random.shuffle(cues_for_block_list)
                if (_check_max_consecutive_items(cues_for_block_list, cue_target_label, max_consecutive_trial_cues) and
                    _check_max_consecutive_items(cues_for_block_list, cue_distractor_label, max_consecutive_trial_cues) and
                    _check_max_consecutive_items(cues_for_block_list, uninformative_cue_label, max_consecutive_trial_cues)):
                    logging.info(f"Block {block_num} (Trial-wise): Found cue sequence meeting max consecutive constraint "
                                 f"for all cue types after {attempt + 1} shuffles.")
                    found_valid_sequence = True
                    break

            if not found_valid_sequence and n_total_trials > 0:
                 logging.warning(f"Block {block_num} (Trial-wise): Could not find cue sequence meeting "
                                f"max_consecutive_trial_cues={max_consecutive_trial_cues} for all cue types "
                                f"after {max_shuffling_attempts} attempts. Using last shuffled sequence.")

        if len(cues_for_block_list) == n_total_trials:
            df["CueInstruction"] = cues_for_block_list
        elif n_total_trials > 0:
            logging.error(
                f"Block {block_num} (Trial-wise): Mismatch in length of generated cues ({len(cues_for_block_list)}) "
                f"and total trials ({n_total_trials}). This is a bug. Filling with error.")
            df["CueInstruction"] = "error_trial_wise_assignment"

    else:
        # --- BLOCK-WISE CUEING LOGIC (Odd Subjects) ---
        logging.info(f"Block {block_num}: Applying BLOCK-WISE cueing strategy (Odd Subject).")

        cue_target_stimulus_this_block: bool
        if block_num % 2 == 0:  # Even block number for an odd subject
            cue_target_stimulus_this_block = False  # Distractor cueing
        else:  # Odd block number for an odd subject
            cue_target_stimulus_this_block = True  # Target cueing

        # Define the specific informative cue label for this block type (target or distractor cueing)
        block_specific_informative_cue: str
        if cue_target_stimulus_this_block:
            block_specific_informative_cue = cue_target_label
        else:
            block_specific_informative_cue = cue_distractor_label
        # uninformative_cue_label is already defined globally within the function

        logging.info(
            f"Block {block_num}: Cueing strategy set to {'TARGETS' if cue_target_stimulus_this_block else 'DISTRACTORS'}.")
        logging.info(
            f"Block {block_num}: Informative cue label for this block: '{block_specific_informative_cue}', Uninformative: '{uninformative_cue_label}'.")
        logging.info(f"Block {block_num}: Prop informative: {prop_informative*100:.0f}%. Max consecutive informative: {max_consecutive_block_cues}.")

        if cue_target_stimulus_this_block:
            # --- TARGET CUEING BLOCK LOGIC (for this block, odd subject) ---
            n_total_trials = len(df)
            logging.info(
                f"Block {block_num} (Target Cues - Odd Subject): Applying {prop_informative * 100:.0f}/{(1 - prop_informative) * 100:.0f} informative/neutral split to all {n_total_trials} trials.")

            if n_total_trials == 0:
                logging.warning(
                    f"Block {block_num} (Target Cues - Odd Subject): DataFrame is empty. No cues to assign.")
                return df

            n_informative_total = int(round(prop_informative * n_total_trials))
            n_uninformative_total = n_total_trials - n_informative_total

            logging.info(f"Block {block_num} (Target Cues - Odd Subject): For all {n_total_trials} trials: "
                         f"{n_informative_total} informative ('{block_specific_informative_cue}'), {n_uninformative_total} neutral ('{uninformative_cue_label}'). ")

            cues_for_block_prototype = ([block_specific_informative_cue] * n_informative_total +
                                        [uninformative_cue_label] * n_uninformative_total)
            cues_for_block_list = list(cues_for_block_prototype)

            if n_informative_total > 0 and n_informative_total > max_consecutive_block_cues:
                min_uninformative_needed = (n_informative_total - 1) // max_consecutive_block_cues if n_informative_total > 0 else 0
                if n_uninformative_total < min_uninformative_needed:
                    logging.warning(
                        f"Block {block_num} (Target Cues - Odd Subject): Potentially not enough uninformative cues ({n_uninformative_total}) "
                        f"to strictly enforce max_consecutive_block_cues={max_consecutive_block_cues} "
                        f"for {n_informative_total} informative cues. (Need at least {min_uninformative_needed}). "
                        f"Will attempt to shuffle but constraint might not be met."
                    )
                max_shuffling_attempts = 200
                found_valid_sequence = False
                for attempt in range(max_shuffling_attempts):
                    np.random.shuffle(cues_for_block_list)
                    if _check_max_consecutive_items(cues_for_block_list, block_specific_informative_cue,
                                                    max_consecutive_block_cues):
                        logging.info(
                            f"Block {block_num} (Target Cues - Odd Subject): Found block-wide cue sequence meeting max consecutive constraint after {attempt + 1} shuffles.")
                        found_valid_sequence = True
                        break
                if not found_valid_sequence:
                    logging.warning(
                        f"Block {block_num} (Target Cues - Odd Subject): Could not find block-wide cue sequence meeting max_consecutive_block_cues={max_consecutive_block_cues} after {max_shuffling_attempts} attempts. Using last shuffled sequence.")
            else:
                np.random.shuffle(cues_for_block_list)
                if n_informative_total > 0:
                    logging.info(
                        f"Block {block_num} (Target Cues - Odd Subject): Max consecutive informative cue constraint ({max_consecutive_block_cues}) trivially met or not applicable for {n_informative_total} informative cues. Shuffled once.")

            if len(cues_for_block_list) == n_total_trials:
                df["CueInstruction"] = cues_for_block_list
            else:
                logging.error(
                    f"Block {block_num} (Target Cues - Odd Subject): Mismatch in length of generated cues ({len(cues_for_block_list)}) and total trials ({n_total_trials}). This is a bug. Filling with neutral.")
                df["CueInstruction"] = uninformative_cue_label
        else:
            # --- DISTRACTOR CUEING BLOCK LOGIC (for this block, odd subject) ---
            logging.info(
                f"Block {block_num} (Distractor Cues - Odd Subject): Applying {prop_informative * 100:.0f}/{(1 - prop_informative) * 100:.0f} informative/neutral split to SingletonPresent==1 trials only.")
            sp_trials_mask = df["SingletonPresent"] == 1
            n_sp_trials = sp_trials_mask.sum()

            if n_sp_trials > 0:
                n_informative_for_sp = int(round(prop_informative * n_sp_trials))
                n_uninformative_for_sp = n_sp_trials - n_informative_for_sp

                logging.info(
                    f"Block {block_num} (Distractor Cues - Odd Subject): For {n_sp_trials} SingletonPresent trials: "
                    f"{n_informative_for_sp} informative ('{block_specific_informative_cue}'), {n_uninformative_for_sp} neutral ('{uninformative_cue_label}'). "
                    f"Max consecutive informative: {max_consecutive_block_cues}.")

                cues_for_sp_prototype = ([block_specific_informative_cue] * n_informative_for_sp +
                                         [uninformative_cue_label] * n_uninformative_for_sp)
                cues_for_sp_list = list(cues_for_sp_prototype)

                if n_informative_for_sp > 0 and n_informative_for_sp > max_consecutive_block_cues:
                    min_uninformative_needed = (n_informative_for_sp - 1) // max_consecutive_block_cues if n_informative_for_sp > 0 else 0
                    if n_uninformative_for_sp < min_uninformative_needed:
                        logging.warning(
                            f"Block {block_num} (Distractor Cues - SP - Odd Subject): Potentially not enough uninformative cues ({n_uninformative_for_sp}) "
                            f"to strictly enforce max_consecutive_block_cues={max_consecutive_block_cues} "
                            f"for {n_informative_for_sp} informative cues. (Need at least {min_uninformative_needed}). "
                            f"Will attempt to shuffle but constraint might not be met."
                        )
                    max_shuffling_attempts = 200
                    found_valid_sequence = False
                    for attempt in range(max_shuffling_attempts):
                        np.random.shuffle(cues_for_sp_list)
                        if _check_max_consecutive_items(cues_for_sp_list, block_specific_informative_cue,
                                                        max_consecutive_block_cues):
                            logging.info(
                                f"Block {block_num} (Distractor Cues - SP - Odd Subject): Found SP cue sequence meeting max consecutive constraint "
                                f"after {attempt + 1} shuffles."
                            )
                            found_valid_sequence = True
                            break
                    if not found_valid_sequence:
                        logging.warning(
                            f"Block {block_num} (Distractor Cues - SP - Odd Subject): Could not find SP cue sequence meeting "
                            f"max_consecutive_block_cues={max_consecutive_block_cues} "
                            f"after {max_shuffling_attempts} attempts. Using last shuffled sequence. "
                            f"Counts: {n_informative_for_sp} informative, {n_uninformative_for_sp} uninformative."
                        )
                else:
                    np.random.shuffle(cues_for_sp_list)
                    if n_informative_for_sp > 0:
                        logging.info(
                            f"Block {block_num} (Distractor Cues - SP - Odd Subject): Max consecutive informative cue constraint ({max_consecutive_block_cues}) "
                            f"is trivially met or not applicable for {n_informative_for_sp} informative cues. Shuffled once."
                        )

                if len(cues_for_sp_list) == n_sp_trials:
                    df.loc[sp_trials_mask, "CueInstruction"] = cues_for_sp_list
                elif n_sp_trials > 0:
                    logging.error(
                        f"Block {block_num} (Distractor Cues - SP - Odd Subject): Mismatch in length of generated SP cues ({len(cues_for_sp_list)}) "
                        f"and number of SP trials ({n_sp_trials}). This is a bug. SP cues not assigned to these trials.")
            else:
                logging.info(
                    f"Block {block_num} (Distractor Cues - Odd Subject): No SingletonPresent == 1 trials found. "
                    f"No SP-specific informative/neutral cues to generate.")

            sa_trials_mask = df["SingletonPresent"] == 0
            df.loc[sa_trials_mask, "CueInstruction"] = uninformative_cue_label
            logging.info(
                f"Block {block_num} (Distractor Cues - Odd Subject): Assigned '{uninformative_cue_label}' to {sa_trials_mask.sum()} SingletonPresent==0 trials.")

    if df["CueInstruction"].isna().any():
        default_fallback_cue = uninformative_cue_label
        logging.warning(
            f"Block {block_num}: Some CueInstructions were still NA after main assignment logic. Defaulting them to '{default_fallback_cue}'.")
        df["CueInstruction"].fillna(default_fallback_cue, inplace=True)

    if df["CueInstruction"].isna().any():
        logging.error(
            f"CRITICAL - Block {block_num}: CueInstruction column still contains NA values after processing and fallback!")

    counts = df["CueInstruction"].value_counts(dropna=False)
    logging.info(f"Final cue instruction distribution for block {block_num}: {counts.to_dict()}")

    return df


def precompute_sequence(subject_id, block, settings, logging_level="INFO", compute_snr=False):
    # get relevant params from settings
    samplerate = settings["session"]["samplerate"]
    freefield = settings["mode"]['freefield']
    # --- LOGGING SETUP ---
    # Base path for all sequence-related data, taken from settings
    subject_sequence_base_path = settings["filepaths"]["sequences"]

    # Construct the path for the logs directory
    log_dir_path = os.path.join(subject_sequence_base_path, "logs")

    try:
        # Ensure the logs directory exists; create it if it doesn't
        os.makedirs(log_dir_path, exist_ok=True)
    except OSError as e:
        # Fallback if directory creation fails (e.g., permissions)
        print(f"CRITICAL: Could not create log directory {log_dir_path}. Error: {e}")
        # Optionally, raise the error or exit if logging is critical
        # For now, we'll let basicConfig try, but it will likely fail to create the file.

    # Construct the full path to the log file
    log_file_path = os.path.join(log_dir_path, f"sub-{subject_id}_trial_sequence_log.txt")

    # Remove any existing handlers from the root logger
    # This is important if this function could be called multiple times in the same Python session
    # to prevent duplicate log messages or multiple file handlers.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close() # Close the handler before removing

    # Configure logging to write to the specified file
    logging.basicConfig(filename=log_file_path,
                        level=logging_level,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filemode='a')  # 'a' for append, so logs from multiple runs/blocks are kept

    logging.info(f"Logging initialized. Log file: {log_file_path}")
    # determine start of function
    start_time = time.time()
    if compute_snr:
        snr_container = dict(snr_left=[], snr_right=[], signal_loc=[])

    subject_sequence_base_path = settings["filepaths"]["sequences"]

    # determine how many trials
    n_trials = settings["session"]["n_trials"]
    # load conditions file
    df_conditions = pd.read_csv(f"all_combinations_{settings['session']['n_locations']}"
                                f"_loudspeakers_{settings['session']['n_digits']}_digits.csv")
    # retrieve sound level to adjust sounds to
    soundlvl = settings["session"]["level"]
    n_blocks = settings["session"]["n_blocks"]
    prop_distractor_present_trials = settings["session"]["prop_distractor_present_trials"]

    # load sounds
    singletons = [slab.Sound.read(f"stimuli/distractors_{settings['session']['distractor_type']}/{x}")
                  for x in os.listdir(f"stimuli/distractors_{settings['session']['distractor_type']}")]
    targets = [slab.Sound.read(f"stimuli/targets_low_30_Hz/{x}") for x in
               os.listdir(f"stimuli/targets_low_30_hz")]  # Ensure path is correct
    others = [slab.Sound.read(f"stimuli/digits_all_250ms/{x}") for x in
              os.listdir(f"stimuli/digits_all_250ms")]

    for s_list in [singletons, targets, others]:
        for sound_item in s_list:
            sound_item.level = soundlvl

    if not freefield:
        singletons = [slab.Binaural(data=x) for x in singletons]
        targets = [slab.Binaural(data=x) for x in targets]
        others = [slab.Binaural(data=x) for x in others]

    # Determine subject properties for cueing and color
    subject_id_int = int(subject_id)
    subject_id_is_even = subject_id_int % 2 == 0 # Used for CueDesignStrategy

    # CueDesignStrategy based on whether subject_id is even or odd
    cue_design_strategy_for_subject = "Trial" if subject_id_is_even else "Block"

    # Color mapping counterbalanced for every two subjects
    # Assumes subject_id_int is 1-based (e.g., 1, 2, 3, ...)
    # Pair group index: (0,0), (1,1), (2,2), ... for subjects (1,2), (3,4), (5,6), ...
    pair_group_index = (subject_id_int - 1) // 2
    if pair_group_index % 2 == 0: # Even pair group (0, 2, 4...)
        color_mapping_for_subject = "target-green-distractor-red"
    else: # Odd pair group (1, 3, 5...)
        color_mapping_for_subject = "target-red-distractor-green"

    logging.info(f"Subject ID: {subject_id}, Integer: {subject_id_int}, Is Even: {subject_id_is_even}")
    logging.info(f"Cue Design Strategy for Subject: {cue_design_strategy_for_subject}")
    logging.info(f"Color Mapping Pair Group Index: {pair_group_index}")
    logging.info(f"Color Mapping for Subject: {color_mapping_for_subject}")

    # Iterate over blocks (starting from the 'block' argument, up to n_blocks)
    for current_block_num in range(block, n_blocks):
        print(f"Running block {current_block_num}")
        logging.info(f"Processing block {current_block_num} for subject {subject_id}")

        dirname = f"sequences/sub-{subject_id}_block_{current_block_num}"
        try:
            os.mkdir(dirname)
        except FileExistsError:
            logging.warning(FileExistsError(f"Directory {dirname} already exists! Moving on ... "))

        sequence, sequence_labels, fitness = make_pygad_trial_sequence(
            fig_path=settings["filepaths"]["sequences"] + "/logs" + f"/sub-{subject_id}_block-{current_block_num}_sequence_fitness.png",
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
                                                                  f"/sub-{subject_id}_sequence_block-{current_block_num}_hist_sp_trials.png",
                                                         prop_distractor_present_trials=prop_distractor_present_trials)
        c_indices = get_element_indices(sequence_final, element="C")
        if len(c_indices) > 1:
            distances_c = np.diff(c_indices)
            sns.histplot(x=distances_c)
            plt.title("Histogram of distances between C trials")
            plt.savefig(
                settings["filepaths"]["sequences"] + "/logs" + f"/sub-{subject_id}_sequence_hist_block{current_block_num}_"
                                                               f"diff_control_trials.png")
            plt.close()
        else:
            logging.info("Not enough C trials to plot distances.")

        trial_sequence = pd.DataFrame()
        prev_target_digit = None
        prev_singleton_digit = None
        prev_target_loc = None
        prev_singleton_loc = None

        for i, element in enumerate(sequence_final):
            if i == 0:
                if "C" not in element:
                    logging.warning(
                        f"First trial is not a control trial. Old: {element}. New: C_SP (or C_SA if SP not possible).")
                    if df_conditions[df_conditions["SingletonPresent"] == True].empty:
                        element = "C_SA"
                    else:
                        element = "C_SP"

            previous_element = sequence_final[i - 1] if i > 0 else None

            while True:
                select_singleton_present = True if "SP" in element else False
                possible_samples = df_conditions[df_conditions["SingletonPresent"] == select_singleton_present]
                if possible_samples.empty:
                    logging.error(
                        f"No conditions found for SingletonPresent={select_singleton_present} (element: {element}). This should not happen if conditions file is complete.")
                    original_element = element
                    if select_singleton_present:
                        element = element.replace("SP", "SA")
                        select_singleton_present = False
                    else:
                        element = element.replace("SA", "SP")
                        select_singleton_present = True
                    possible_samples = df_conditions[df_conditions["SingletonPresent"] == select_singleton_present]
                    if possible_samples.empty:
                        raise ValueError(
                            f"Critial: No conditions for SP or SA. Element: {original_element}. Check conditions file.")
                    logging.warning(
                        f"Switched element from {original_element} to {element} due to no matching conditions.")

                sample = possible_samples.sample()

                if i > 0:
                    if "SP" not in element and (previous_element and "SP" not in previous_element):
                        prev_singleton_loc = None
                        prev_singleton_digit = None
                    if "NP" in element and (previous_element and "NP" in previous_element):
                        logging.debug(f"Consecutive NP elements. Changing {element} to C-equivalent.")
                        element = "C_SP" if "SP" in element else "C_SA"

                valid_choice = False
                if "C" in element:
                    if (sample["TargetDigit"].values[0] != prev_target_digit and
                            (select_singleton_present is False or sample["SingletonDigit"].values[
                                0] != prev_singleton_digit) and
                            sample["TargetLoc"].values[0] != prev_target_loc and
                            (select_singleton_present is False or sample["SingletonLoc"].values[
                                0] != prev_singleton_loc)):
                        sample["Priming"] = 0
                        valid_choice = True
                elif "NP" in element:
                    if select_singleton_present is False or prev_singleton_digit is None or prev_singleton_loc is None:
                        logging.debug(
                            f"Cannot make NP trial (no prev singleton or current is SA). Element: {element}. Trying C.")
                        continue
                    if (sample["TargetDigit"].values[0] == prev_singleton_digit and
                            sample["TargetLoc"].values[0] == prev_singleton_loc):
                        sample["Priming"] = -1
                        valid_choice = True
                elif "PP" in element:
                    if prev_target_digit is None or prev_target_loc is None:
                        logging.debug(f"Cannot make PP trial (no prev target). Element: {element}. Trying C.")
                        continue
                    if (sample["TargetDigit"].values[0] == prev_target_digit and
                            sample["TargetLoc"].values[0] == prev_target_loc):
                        sample["Priming"] = 1
                        valid_choice = True

                if valid_choice:
                    break

            logging.debug(
                f"Block {current_block_num}, Trial {i}: Selected condition for {element} (Priming: {sample['Priming'].values[0]})")
            prev_target_digit = sample["TargetDigit"].values[0]
            prev_target_loc = sample["TargetLoc"].values[0]
            if select_singleton_present:
                prev_singleton_digit = sample["SingletonDigit"].values[0]
                prev_singleton_loc = sample["SingletonLoc"].values[0]
            else:
                prev_singleton_digit = None
                prev_singleton_loc = None

            trial_sequence = pd.concat([trial_sequence, sample], ignore_index=True)

        trial_sequence.reset_index(drop=True, inplace=True)
        print_final_traits(trial_sequence)

        trial_sequence["ITI-Jitter"] = generate_balanced_jitter(trial_sequence, iti=settings["session"]["iti"],
                                                                mode="ITI")
        trial_sequence["ITI-Jitter"] = round(trial_sequence["ITI-Jitter"], 3)

        trial_sequence["cue_stim_delay_jitter"] = generate_balanced_jitter(trial_sequence, iti=settings["session"]["cue_stim_delay"],
                                                                           mode="cue_stim_delay")
        trial_sequence["cue_stim_delay_jitter"] = round(trial_sequence["cue_stim_delay_jitter"], 3)

        trial_sequence["CueDesignStrategy"] = cue_design_strategy_for_subject
        trial_sequence["Color"] = color_mapping_for_subject

        cue_prop_informative = settings["session"]["cue_prop_informative"]
        max_consecutive_block_cues = settings["session"]["max_consecutive_informative"]
        max_consecutive_trial_cues = settings["session"].get("max_consecutive_trial_type_cues", 5)

        trial_sequence = insert_pseudo_randomized_cues(
            trial_sequence,
            block_num=current_block_num,
            subject_is_even=subject_id_is_even, # This remains based on individual subject ID even/odd
            prop_informative=cue_prop_informative,
            max_consecutive_block_cues=max_consecutive_block_cues,
            max_consecutive_trial_cues=max_consecutive_trial_cues
        )

        file_name = f"sequences/sub-{subject_id}_block_{current_block_num}.csv"
        trial_sequence.to_csv(file_name, index=False)

        logging.info(f"Saved trial sequence to {file_name}")
        logging.info(f"Precomputing trial sounds for subject {subject_id}, block {current_block_num} ... ")

        sound_sequence = []
        for i, row in trial_sequence.iterrows():
            logging.debug(f"Precompute trialsound for trial {i}, block {current_block_num} ... ")
            if not freefield:
                trialsound_base = slab.Binaural.silence(duration=settings["session"]["stimulus_duration"],
                                                        samplerate=samplerate)
            elif freefield:
                num_samples = int(samplerate * settings["session"]["stimulus_duration"])
                num_possible_locations = settings['session']['n_locations']
                trialsound_data = np.zeros((num_possible_locations, num_samples))

            targetval = int(row["TargetDigit"])
            targetsound = deepcopy(targets[targetval - 1])
            targetsound.level = soundlvl
            targetloc = row["TargetLoc"]
            targetsound_rendered_for_snr = None

            if not freefield:
                azimuth, ele = SPACE_ENCODER[targetloc]
                targetsound_rendered = spatialize(targetsound, azi=azimuth, ele=ele)
                if targetsound_rendered.n_samples != trialsound_base.n_samples:
                    targetsound_rendered = targetsound_rendered.resize(trialsound_base.n_samples)
                trialsound_base.data += targetsound_rendered.data
                targetsound_rendered_for_snr = targetsound_rendered
            else:
                speaker_idx = int(targetloc - 1)
                if 0 <= speaker_idx < trialsound_data.shape[0]:
                    sound_data_mono = targetsound.data
                    if targetsound.n_channels > 1:
                        sound_data_mono = targetsound.data[:, 0]
                    if len(sound_data_mono) > num_samples:
                        sound_data_mono = sound_data_mono[:num_samples]
                    elif len(sound_data_mono) < num_samples:
                        sound_data_mono = np.pad(sound_data_mono, (0, num_samples - len(sound_data_mono)))
                    trialsound_data[speaker_idx, :] = sound_data_mono
                else:
                    logging.error(f"TargetLoc {targetloc} is out of bounds for freefield speaker array.")

            noise_components_for_snr = []

            if row["SingletonPresent"] == 1:
                singletonsound = deepcopy(singletons[int(row["SingletonDigit"]) - 1])
                singletonsound.level = soundlvl
                singletonloc = row["SingletonLoc"]
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[singletonloc]
                    singletonsound_rendered = spatialize(singletonsound, azi=azimuth, ele=ele)
                    if singletonsound_rendered.n_samples != trialsound_base.n_samples:
                        singletonsound_rendered = singletonsound_rendered.resize(trialsound_base.n_samples)
                    trialsound_base.data += singletonsound_rendered.data
                    noise_components_for_snr.append(singletonsound_rendered)
                else:
                    speaker_idx = int(singletonloc - 1)
                    if 0 <= speaker_idx < trialsound_data.shape[0]:
                        sound_data_mono = singletonsound.data
                        if singletonsound.n_channels > 1: sound_data_mono = sound_data_mono[:, 0]
                        if len(sound_data_mono) > num_samples:
                            sound_data_mono = sound_data_mono[:num_samples]
                        elif len(sound_data_mono) < num_samples:
                            sound_data_mono = np.pad(sound_data_mono, (0, num_samples - len(sound_data_mono)))
                        trialsound_data[speaker_idx, :] += sound_data_mono
                    else:
                        logging.error(f"SingletonLoc {singletonloc} out of bounds.")

                digit2sound = deepcopy(others[int(row["Non-Singleton2Digit"]) - 1])
                digit2sound.level = soundlvl
                digit2loc = row["Non-Singleton2Loc"]
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[digit2loc]
                    digit2sound_rendered = spatialize(digit2sound, azi=azimuth, ele=ele)
                    if digit2sound_rendered.n_samples != trialsound_base.n_samples:
                        digit2sound_rendered = digit2sound_rendered.resize(trialsound_base.n_samples)
                    trialsound_base.data += digit2sound_rendered.data
                    noise_components_for_snr.append(digit2sound_rendered)
                else:
                    speaker_idx = int(digit2loc - 1)
                    if 0 <= speaker_idx < trialsound_data.shape[0]:
                        sound_data_mono = digit2sound.data
                        if digit2sound.n_channels > 1: sound_data_mono = sound_data_mono[:, 0]
                        if len(sound_data_mono) > num_samples:
                            sound_data_mono = sound_data_mono[:num_samples]
                        elif len(sound_data_mono) < num_samples:
                            sound_data_mono = np.pad(sound_data_mono, (0, num_samples - len(sound_data_mono)))
                        trialsound_data[speaker_idx, :] += sound_data_mono
                    else:
                        logging.error(f"Non-Singleton2Loc {digit2loc} out of bounds.")

            elif row["SingletonPresent"] == 0:
                digit1sound = deepcopy(others[int(row["Non-Singleton1Digit"]) - 1])
                digit1sound.level = soundlvl
                digit1loc = row["Non-Singleton1Loc"]
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[digit1loc]
                    digit1sound_rendered = spatialize(digit1sound, azi=azimuth, ele=ele)
                    if digit1sound_rendered.n_samples != trialsound_base.n_samples:
                        digit1sound_rendered = digit1sound_rendered.resize(trialsound_base.n_samples)
                    trialsound_base.data += digit1sound_rendered.data
                    noise_components_for_snr.append(digit1sound_rendered)
                else:
                    speaker_idx = int(digit1loc - 1)
                    if 0 <= speaker_idx < trialsound_data.shape[0]:
                        sound_data_mono = digit1sound.data
                        if digit1sound.n_channels > 1: sound_data_mono = sound_data_mono[:, 0]
                        if len(sound_data_mono) > num_samples:
                            sound_data_mono = sound_data_mono[:num_samples]
                        elif len(sound_data_mono) < num_samples:
                            sound_data_mono = np.pad(sound_data_mono, (0, num_samples - len(sound_data_mono)))
                        trialsound_data[speaker_idx, :] += sound_data_mono
                    else:
                        logging.error(f"Non-Singleton1Loc {digit1loc} out of bounds.")

                digit2sound = deepcopy(others[int(row["Non-Singleton2Digit"]) - 1])
                digit2sound.level = soundlvl
                digit2loc = row["Non-Singleton2Loc"]
                if not freefield:
                    azimuth, ele = SPACE_ENCODER[digit2loc]
                    digit2sound_rendered = spatialize(digit2sound, azi=azimuth, ele=ele)
                    if digit2sound_rendered.n_samples != trialsound_base.n_samples:
                        digit2sound_rendered = digit2sound_rendered.resize(trialsound_base.n_samples)
                    trialsound_base.data += digit2sound_rendered.data
                    noise_components_for_snr.append(digit2sound_rendered)
                else:
                    speaker_idx = int(digit2loc - 1)
                    if 0 <= speaker_idx < trialsound_data.shape[0]:
                        sound_data_mono = digit2sound.data
                        if digit2sound.n_channels > 1: sound_data_mono = sound_data_mono[:, 0]
                        if len(sound_data_mono) > num_samples:
                            sound_data_mono = sound_data_mono[:num_samples]
                        elif len(sound_data_mono) < num_samples:
                            sound_data_mono = np.pad(sound_data_mono, (0, num_samples - len(sound_data_mono)))
                        trialsound_data[speaker_idx, :] += sound_data_mono
                    else:
                        logging.error(f"Non-Singleton2Loc {digit2loc} out of bounds.")

            if not freefield:
                final_trialsound = slab.Binaural(trialsound_base.data, samplerate=samplerate)
            else:
                final_trialsound = slab.Sound(trialsound_data.T, samplerate=samplerate)

            sound_sequence.append(final_trialsound.ramp(when='both', duration=0.01))

            if compute_snr and not freefield:
                if targetsound_rendered_for_snr and noise_components_for_snr:
                    combined_noise = deepcopy(noise_components_for_snr[0]) # Start with a copy
                    for k in range(1, len(noise_components_for_snr)):
                        combined_noise.data += noise_components_for_snr[k].data

                    snr_left, snr_right = snr_sound_mixture_two_ears(targetsound_rendered_for_snr, combined_noise)
                    snr_container["snr_left"].append(snr_left[0])
                    snr_container["snr_right"].append(snr_right[0])
                    azimuth, _ = SPACE_ENCODER[targetloc]
                    snr_container["signal_loc"].append(azimuth)
                else:
                    logging.warning(f"Skipping SNR for trial {i}, missing sound components.")

        if compute_snr and not freefield:
            df_snr = pd.DataFrame.from_dict(snr_container)
            file_name_snr = os.path.join(dirname, f"sub-{subject_id}_block_{current_block_num}_snr.csv")
            df_snr.to_csv(file_name_snr, index=False)
            snr_container = dict(snr_left=[], snr_right=[], signal_loc=[]) # Reset for next block

        for idx, sound_obj in enumerate(sound_sequence):
            sound_filename = os.path.join(dirname, f"s_{idx}.wav")
            sound_obj.write(filename=sound_filename, normalise=False)
        logging.info(f"Finished writing sounds for block {current_block_num}.")

    end_time = time.time()
    logging.info("DONE generating all blocks for subject.")
    logging.info(f"Total script running time: {(end_time - start_time):.2f} seconds")


# Example of how to add the new setting to your settings dictionary if loaded from YAML
# This would typically be in your config.yaml:
# session:
#   ...
#   max_consecutive_trial_type_cues: 5
#   ...
if "session" not in settings: settings["session"] = {}  # Ensure session key exists
if "max_consecutive_trial_type_cues" not in settings["session"]:
    logging.info("Setting 'max_consecutive_trial_type_cues' not found in config, defaulting to 5.")
    settings["session"]["max_consecutive_trial_type_cues"] = 5

precompute_sequence(subject_id=info["subject_id"], block=info["block"], settings=settings)
