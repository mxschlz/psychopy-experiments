import pandas as pd
import yaml
import argparse
import os
import logging
import random
import Levenshtein
from itertools import combinations
from scipy.stats import binomtest, chisquare


# Configure simple logging for clear output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# --- Helper Functions for Reporting ---

def print_check_header(title):
    """Prints a formatted header for each check section."""
    print("\n" + "=" * 60)
    print(f"CHECK: {title}")
    print("=" * 60)


def print_result(check_name, success, message):
    """Prints a PASS/FAIL result for a specific check."""
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {check_name}: {message}")
    return success


def check_proportions(df, config, alpha=0.05):
    """
    Checks if the proportions of trial types match the config using statistical tests.
    - Chi-Squared Goodness-of-Fit for C, NP, PP proportions.
    - Binomial Test for Singleton-Present proportion.
    """
    print_check_header("Trial Type Proportions (Statistical)")
    n_trials = len(df)
    all_passed = True

    # 1. Priming Type Proportions (C, NP, PP) using Chi-Squared Test
    priming_counts = df['Priming'].value_counts()
    c_count = priming_counts.get(0, 0)
    np_count = priming_counts.get(-1, 0)
    pp_count = priming_counts.get(1, 0)

    observed_counts = [c_count, np_count, pp_count]
    expected_props = [
        config['trial_sequence']['prop_c'],
        config['trial_sequence']['prop_np'],
        config['trial_sequence']['prop_pp']
    ]
    # Ensure proportions sum to 1 for the test
    expected_counts = [p * n_trials for p in expected_props]

    if sum(observed_counts) == sum(expected_counts):
        chi2_stat, p_value = chisquare(f_obs=observed_counts, f_exp=expected_counts)
        # We pass if we FAIL to reject the null hypothesis (that observed matches expected)
        proportions_ok = p_value >= alpha
        # --- CORRECTED LINE ---
        message = (f"Observed [C,NP,PP] = {observed_counts}, Expected ~{[int(ec) for ec in expected_counts]}. "
                   f"p-value = {p_value:.3f}")
        all_passed &= print_result("Priming Type Distribution", proportions_ok, message)
    else:
        all_passed &= print_result("Priming Type Distribution", False, "Mismatch in total trial counts.")

    # 2. Singleton-Present (SP) Proportion using Binomial Test
    sp_count = df['SingletonPresent'].sum()
    expected_sp_prop = 0.5
    # H0: The probability of a trial being Singleton-Present is 0.5
    result = binomtest(k=sp_count, n=n_trials, p=expected_sp_prop)
    p_value_sp = result.pvalue

    sp_ok = p_value_sp >= alpha
    message = (f"Found {sp_count}/{n_trials} SP trials. "
               f"p-value = {p_value_sp:.3f} for expected proportion of {expected_sp_prop:.0%}.")
    all_passed &= print_result("Singleton-Present Proportion", sp_ok, message)

    return all_passed


def check_sequence_rules(df):
    """Checks high-level sequence rules (starts with C, no consecutive priming)."""
    print_check_header("High-Level Sequence Rules")
    all_passed = True

    # 1. Must start with a Control trial
    starts_with_c = df.iloc[0]['Priming'] == 0
    all_passed &= print_result("Starts with Control Trial", starts_with_c,
                               f"First trial is Priming={df.iloc[0]['Priming']} (0=C)")

    # 2. No consecutive NP or PP trials
    consecutive_violations = 0
    priming_sequence = df['Priming'].tolist()
    for i in range(len(priming_sequence) - 1):
        # Priming values are 0 (C), -1 (NP), and 1 (PP)
        if priming_sequence[i] != 0 and priming_sequence[i + 1] != 0:
            consecutive_violations += 1
            logging.warning(f"  - Violation at index {i}: Priming {priming_sequence[i]} -> {priming_sequence[i + 1]}")

    no_consecutive = consecutive_violations == 0
    all_passed &= print_result("No Consecutive NP/PP Trials", no_consecutive,
                               f"Found {consecutive_violations} violations.")

    return all_passed


def check_priming_logic(df):
    """Verifies the trial-to-trial logic for C, NP, and PP conditions."""
    print_check_header("Trial-to-Trial Priming Logic")
    errors = 0

    # Iterate from the second trial, as priming depends on the previous one
    for i in range(1, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i - 1]
        priming_type = current['Priming']

        # Check NP condition: Current target must match previous singleton
        if priming_type == -1:  # NP
            if not (current['TargetDigit'] == prev['SingletonDigit'] and current['TargetLoc'] == prev['SingletonLoc']):
                errors += 1
                logging.warning(
                    f"  - NP Logic FAIL @ trial {i}: Current Target ({current['TargetDigit']} @ L{current['TargetLoc']}) "
                    f"!= Previous Singleton ({prev['SingletonDigit']} @ L{prev['SingletonLoc']})")

        # Check PP condition: Current target must match previous target
        elif priming_type == 1:  # PP
            if not (current['TargetDigit'] == prev['TargetDigit'] and current['TargetLoc'] == prev['TargetLoc']):
                errors += 1
                logging.warning(
                    f"  - PP Logic FAIL @ trial {i}: Current Target ({current['TargetDigit']} @ L{current['TargetLoc']}) "
                    f"!= Previous Target ({prev['TargetDigit']} @ L{prev['TargetLoc']})")

        # Check C condition: Must not be an NP or PP trial (or other obvious repetition)
        elif priming_type == 0:  # C
            is_pp_repeat = (current['TargetDigit'] == prev['TargetDigit'] and current['TargetLoc'] == prev['TargetLoc'])
            is_np_repeat = (current['TargetDigit'] == prev['SingletonDigit'] and current['TargetLoc'] == prev[
                'SingletonLoc'])

            if is_pp_repeat or is_np_repeat:
                errors += 1
                logging.warning(f"  - C Logic FAIL @ trial {i}: Found a priming repetition in a Control trial.")

    success = errors == 0
    return print_result("Priming Logic Correctness", success, f"Found {errors} logic errors across the sequence.")


def check_trial_integrity(df):
    """Checks that within a single trial, locations and digits are unique."""
    print_check_header("Within-Trial Integrity (Unique Locations/Digits)")
    errors = 0

    for i, row in df.iterrows():
        if row['SingletonPresent'] == 1:
            locs = [row['TargetLoc'], row['SingletonLoc'], row['Non-Singleton2Loc']]
            digits = [row['TargetDigit'], row['SingletonDigit'], row['Non-Singleton2Digit']]
        else:  # Singleton Absent
            locs = [row['TargetLoc'], row['Non-Singleton1Loc'], row['Non-Singleton2Loc']]
            digits = [row['TargetDigit'], row['Non-Singleton1Digit'], row['Non-Singleton2Digit']]

        if len(locs) != len(set(locs)):
            errors += 1
            logging.warning(f"  - Location repetition on trial {i}: {locs}")
        if len(digits) != len(set(digits)):
            errors += 1
            logging.warning(f"  - Digit repetition on trial {i}: {digits}")

    success = errors == 0
    return print_result("Unique locations/digits per trial", success, f"Found {errors} integrity violations.")


def evaluate_sequence(subject_id, block, config):
    """Main evaluation function to run all checks."""
    print(f"\n--- Evaluating Sequence for Subject {subject_id}, Block {block} ---")

    # Construct file path and load data
    seq_dir = config['filepaths']['sequences']
    file_name = f"sci-{subject_id}_block_{block}.csv"
    file_path = os.path.join(seq_dir, file_name)

    if not os.path.exists(file_path):
        logging.error(f"Sequence file not found: {file_path}")
        return

    df = pd.read_csv(file_path)
    logging.info(f"Successfully loaded sequence file: {file_path}")

    # Run all checks and store results
    results = [
        check_proportions(df, config),
        check_sequence_rules(df),
        check_priming_logic(df),
        check_distractor_bias_and_labels(df, subject_id, config),
        check_trial_integrity(df)
    ]

    # Final Summary
    print("\n" + "*" * 60)
    print("EVALUATION SUMMARY")
    print("*" * 60)
    if all(results):
        print("✅ All checks passed. The sequence meets all specified constraints.")
    else:
        print("❌ Some checks failed. Please review the log above for details.")
    print("*" * 60)

def check_distractor_bias_and_labels(df, subject_id, config, alpha=0.05):
    """
    Checks the distractor location bias and verifies the 'DistractorProb' column.
    1. Verifies the 'DistractorProb' column labels are correct against trial data.
    2. Checks the proportion of high-probability trials is ~66% using a Binomial Test.
    """
    print_check_header("Distractor Bias and Probability Labeling (Statistical)")
    all_passed = True

    # --- 1. Check for column presence ---
    if 'DistractorProb' not in df.columns:
        print_result("Distractor Checks", False, "'DistractorProb' column is missing from the sequence file.")
        return False  # Cannot proceed

    # --- 2. Verify label correctness for every trial ---
    labeling_errors = 0
    is_even = subject_id % 2 == 0
    n_locations = config['session']['n_locations']

    biased_loc = -1  # Sentinel value for when bias is not applicable
    if n_locations >= 3:
        biased_loc = 1 if is_even else 3

    for i, row in df.iterrows():
        is_sp = row['SingletonPresent'] == 1
        label = row['DistractorProb']
        actual_loc = row['SingletonLoc']

        if is_sp:
            expected_label = 'low-probability'
            if actual_loc == biased_loc and biased_loc != -1:
                expected_label = 'high-probability'
            if label != expected_label:
                labeling_errors += 1
                logging.warning(
                    f"  - Labeling FAIL @ trial {i}: Expected '{expected_label}' but found '{label}'. "
                    f"(Biased loc: {biased_loc if biased_loc != -1 else 'N/A'}, Actual loc: {actual_loc})"
                )
        else:  # Singleton-absent
            if label != 'distractor-absent':
                labeling_errors += 1
                logging.warning(
                    f"  - Labeling FAIL @ trial {i}: Expected 'distractor-absent' for SA trial but found '{label}'."
                )

    labels_ok = labeling_errors == 0
    all_passed &= print_result("Correct Labeling in 'DistractorProb' Column", labels_ok,
                               f"Found {labeling_errors} labeling errors.")

    # --- 3. Check the statistical proportion of high-probability trials ---
    if n_locations < 3:
        # ... (this part is unchanged)
        return all_passed

    sp_trials = df[df['SingletonPresent'] == 1]
    if sp_trials.empty:
        # ... (this part is unchanged)
        return all_passed

    n_sp_trials = len(sp_trials)
    n_high_prob = (sp_trials['DistractorProb'] == 'high-probability').sum()
    expected_prop = 0.66

    # Perform Binomial Test
    # H0: The probability of a distractor appearing at the biased location is 0.66
    result = binomtest(k=n_high_prob, n=n_sp_trials, p=expected_prop)
    p_value_bias = result.pvalue
    bias_ok = p_value_bias >= alpha

    subject_type = "even" if is_even else "odd"
    message = (
        f"Subject {subject_id} ({subject_type}): Found {n_high_prob}/{n_sp_trials} high-prob trials. "
        f"p-value = {p_value_bias:.3f} for expected proportion of {expected_prop:.0%}."
    )

    all_passed &= print_result("High-Probability Bias Proportion", bias_ok, message)

    return all_passed

def analyze_directory_randomness(config):
    """
    Analyzes all sequences in a directory to measure their 'randomness'.

    Compares each sequence's priming order to a randomly shuffled sequence
    with the same proportions, using Levenshtein distance. A lower distance
    suggests the sequence is closer to a random shuffle, while a higher
    distance indicates more structure imposed by the generation algorithm.
    """
    print_check_header("Sequence Randomness Analysis (Levenshtein Distance)")

    seq_dir = config['filepaths']['sequences']
    if not os.path.isdir(seq_dir):
        logging.error(f"Sequence directory not found: {seq_dir}")
        return

    try:
        sequence_files = [f for f in os.listdir(seq_dir) if f.endswith('.csv') and f.startswith('sci-')]
    except FileNotFoundError:
        print_result("Directory Scan", False, f"Could not find or access the directory: {seq_dir}")
        return

    if not sequence_files:
        print_result("Directory Scan", False, f"No sequence files found in {seq_dir}")
        return

    print(f"Found {len(sequence_files)} sequence files in '{seq_dir}'.")
    distances = []
    priming_map = {0: 'C', 1: 'P', -1: 'N'}

    for file_name in sequence_files:
        file_path = os.path.join(seq_dir, file_name)
        df = pd.read_csv(file_path)
        n_trials = len(df)

        # 1. Create the actual sequence string from the 'Priming' column
        actual_sequence_list = df['Priming'].map(priming_map).tolist()
        actual_sequence_str = "".join(actual_sequence_list)

        # 2. Create a baseline "fully random" sequence by shuffling the actual elements.
        # This provides a perfect baseline by controlling for the number of C, P, and N trials.
        random_sequence_list = actual_sequence_list.copy()
        random.shuffle(random_sequence_list)
        random_sequence_str = "".join(random_sequence_list)

        # 3. Calculate Levenshtein distance
        distance = Levenshtein.distance(actual_sequence_str, random_sequence_str)
        distances.append(distance)

        # Normalize distance by sequence length for easier comparison across different lengths
        normalized_distance = distance / n_trials if n_trials > 0 else 0
        print(f"  - {file_name}: Levenshtein distance = {distance} (Normalized: {normalized_distance:.2f})")

    # 4. Report summary statistics
    if distances:
        avg_dist = sum(distances) / len(distances)
        max_dist = max(distances)
        min_dist = min(distances)
        print("\n--- Summary ---")
        print(f"Average Levenshtein Distance: {avg_dist:.2f}")
        print(f"Min / Max Distance: {min_dist} / {max_dist}")
        print("\nInterpretation: This distance measures the edits needed to turn the generated")
        print("sequence into a random shuffle of itself. A higher distance implies more structure")
        print("due to constraints (e.g., 'no consecutive NP/PP') compared to random chance.")
    else:
        print("No distances were calculated.")

def analyze_inter_sequence_similarity(config):
    """
    Analyzes similarity between all pairs of sequences in a directory.

    This check addresses the concern that the generation algorithm might produce
    sequences that are too similar to each other across different subjects.
    A high average distance indicates good variability between sequences.
    """
    print_check_header("Inter-Sequence Similarity Analysis (Pairwise Levenshtein)")

    seq_dir = config['filepaths']['sequences']
    try:
        sequence_files = [f for f in os.listdir(seq_dir) if f.endswith('.csv') and f.startswith('sci-')]
    except FileNotFoundError:
        print_result("Directory Scan", False, f"Could not find or access the directory: {seq_dir}")
        return

    if len(sequence_files) < 2:
        print("Skipping analysis: Need at least two sequence files to compare.")
        return

    print(f"Found {len(sequence_files)} sequence files. Comparing all unique pairs...")
    priming_map = {0: 'C', 1: 'P', -1: 'N'}
    sequence_strings = []

    # 1. Load all sequence strings into a list
    for file_name in sequence_files:
        file_path = os.path.join(seq_dir, file_name)
        df = pd.read_csv(file_path)
        actual_sequence_list = df['Priming'].map(priming_map).tolist()
        sequence_strings.append("".join(actual_sequence_list))

    # 2. Calculate Levenshtein distance for all unique pairs
    distances = []
    # Use itertools.combinations to efficiently get all unique pairs
    for seq1, seq2 in combinations(sequence_strings, 2):
        distance = Levenshtein.distance(seq1, seq2)
        distances.append(distance)

    # 3. Report summary statistics
    if distances:
        avg_dist = sum(distances) / len(distances)
        max_dist = max(distances)
        min_dist = min(distances)
        n_pairs = len(distances)

        print(f"\n--- Summary (based on {n_pairs} comparisons) ---")
        print(f"Average Levenshtein Distance between sequences: {avg_dist:.2f}")
        print(f"Min / Max Distance between any two sequences: {min_dist} / {max_dist}")

        print("\nInterpretation: This measures how different the trial orders are from each other.")
        if min_dist > (len(sequence_strings[0]) * 0.1): # If min distance is > 10% of sequence length
             print("✅ The minimum distance is high, providing strong evidence that your sequences are unique.")
             print("   Even the two most similar sequences are still significantly different.")
        else:
             print("⚠️ The minimum distance is low. This suggests some sequences may be very similar to each other.")
             print("   Review the files to see if the similarity is problematic for your experiment.")
    else:
        print("No pairwise distances were calculated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate generated trial sequences. \n\n"
                    "Modes of operation:\n"
                    "1. Single File: Evaluate one sequence file for all constraints.\n"
                    "   Example: python evaluate_trial_sequence.py -s 10 -b 0\n\n"
                    "2. Randomness Analysis: Check how structured each sequence is against a random baseline.\n"
                    "   Example: python evaluate_trial_sequence.py --randomness\n\n"
                    "3. Similarity Analysis: Check how different sequences are from EACH OTHER.\n"
                    "   Example: python evaluate_trial_sequence.py --similarity",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-c", "--config", type=str, default="config.yaml", help="Path to the configuration file.")

    # Group for single evaluation
    single_eval_group = parser.add_argument_group('Single Sequence Evaluation')
    single_eval_group.add_argument("-s", "--subject", type=int, help="Subject ID (e.g., 10).")
    single_eval_group.add_argument("-b", "--block", type=int, help="Block number (e.g., 0).")

    # Group for directory analysis
    dir_analysis_group = parser.add_argument_group('Directory-Wide Analyses')
    dir_analysis_group.add_argument("--randomness", action="store_true",
                                    help="Analyze internal structure of all sequences using Levenshtein distance.")
    dir_analysis_group.add_argument("--similarity", action="store_true",
                                    help="Analyze similarity between all pairs of sequences in the directory.")

    args = parser.parse_args()

    # --- Main Logic ---
    try:
        with open(args.config) as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file not found at '{args.config}'. Aborting.")
        exit(1)

    run_single_eval = args.subject is not None and args.block is not None
    run_randomness_analysis = args.randomness
    run_similarity_analysis = args.similarity

    if not any([run_single_eval, run_randomness_analysis, run_similarity_analysis]):
        parser.print_help()
        logging.error("\nNo action specified. Please provide an evaluation mode.")
        exit(1)

    if run_single_eval:
        evaluate_sequence(subject_id=args.subject, block=args.block, config=config)

    if run_randomness_analysis:
        if run_single_eval: print("\n" + "#" * 70)
        analyze_directory_randomness(config)

    if run_similarity_analysis:
        if run_single_eval or run_randomness_analysis: print("\n" + "#" * 70)
        analyze_inter_sequence_similarity(config)
