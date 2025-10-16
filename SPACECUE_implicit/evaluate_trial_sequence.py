import pandas as pd
import yaml
import argparse
import os
import logging
from scipy.stats import binomtest
from itertools import combinations
import Levenshtein
import random

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


# --- Core Evaluation Functions ---

def check_proportions_and_rules(df, config, alpha=0.05):
    """
    Checks the core rules defined by the new genetic algorithm.
    1. Proportion of Singleton-Present (SP) trials.
    2. Rule of max 5 consecutive SP trials.
    3. Reports the incidental priming proportions.
    """
    print_check_header("GA Rules and Proportions (Statistical)")
    n_trials = len(df)
    all_passed = True

    # 1. Singleton-Present (SP) Proportion using Binomial Test
    sp_count = df['SingletonPresent'].sum()
    expected_sp_prop = config['trial_sequence']['prop_sp']
    # H0: The probability of a trial being SP matches the configured proportion.
    result = binomtest(k=sp_count, n=n_trials, p=expected_sp_prop)
    p_value_sp = result.pvalue

    sp_ok = p_value_sp >= alpha
    message = (f"Found {sp_count}/{n_trials} SP trials. "
               f"p-value = {p_value_sp:.3f} for expected proportion of {expected_sp_prop:.0%}.")
    all_passed &= print_result("Singleton-Present Proportion", sp_ok, message)

    # 2. Check for max consecutive SP trials
    max_consecutive_allowed = 5
    max_found = 0
    current_consecutive = 0
    for is_sp in df['SingletonPresent']:
        if is_sp == 1:
            current_consecutive += 1
        else:
            max_found = max(max_found, current_consecutive)
            current_consecutive = 0
    max_found = max(max_found, current_consecutive)  # Final check for sequences ending in SP

    consecutive_ok = max_found <= max_consecutive_allowed
    message = f"Found a maximum of {max_found} consecutive SP trials (Rule: <= {max_consecutive_allowed})."
    all_passed &= print_result("Max Consecutive SP Trials", consecutive_ok, message)

    # 3. Report incidental priming proportions (no test, just info)
    print("\n--- Incidental Priming Report (Informational) ---")
    priming_counts = df['Priming'].value_counts()
    c_count = priming_counts.get(0, 0)
    np_count = priming_counts.get(-1, 0)
    pp_count = priming_counts.get(1, 0)
    print(f"Control (C) by chance: {c_count} ({c_count/n_trials:.1%})")
    print(f"Negative Priming (NP) by chance: {np_count} ({np_count/n_trials:.1%})")
    print(f"Positive Priming (PP) by chance: {pp_count} ({pp_count/n_trials:.1%})")

    return all_passed


def verify_priming_labels(df):
    """Verifies the post-hoc trial-to-trial labeling for C, NP, and PP conditions."""
    print_check_header("Post-Hoc Priming Label Verification")
    errors = 0

    # Iterate from the second trial, as priming depends on the previous one
    for i in range(1, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i - 1]
        priming_label = current['Priming']

        is_pp_repeat = (current['TargetDigit'] == prev['TargetDigit'] and current['TargetLoc'] == prev['TargetLoc'])
        is_np_repeat = (prev['SingletonPresent'] == 1 and
                        current['TargetDigit'] == prev['SingletonDigit'] and
                        current['TargetLoc'] == prev['SingletonLoc'])

        # Check NP label
        if priming_label == -1 and not is_np_repeat:
            errors += 1
            logging.warning(f"  - NP Label FAIL @ trial {i}: Labeled NP, but logic does not match.")
        # Check PP label
        elif priming_label == 1 and not is_pp_repeat:
            errors += 1
            logging.warning(f"  - PP Label FAIL @ trial {i}: Labeled PP, but logic does not match.")
        # Check C label
        elif priming_label == 0 and (is_pp_repeat or is_np_repeat):
            errors += 1
            logging.warning(f"  - C Label FAIL @ trial {i}: Labeled C, but a priming condition was met.")

    success = errors == 0
    return print_result("Priming Label Correctness", success, f"Found {errors} labeling errors across the sequence.")


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

        # Filter out NaN values which can occur in non-singleton columns
        locs = [l for l in locs if pd.notna(l)]
        digits = [d for d in digits if pd.notna(d)]

        if len(locs) != len(set(locs)):
            errors += 1
            logging.warning(f"  - Location repetition on trial {i}: {locs}")
        if len(digits) != len(set(digits)):
            errors += 1
            logging.warning(f"  - Digit repetition on trial {i}: {digits}")

    success = errors == 0
    return print_result("Unique locations/digits per trial", success, f"Found {errors} integrity violations.")


def check_distractor_bias_and_labels(df, subject_id, config, alpha=0.05):
    """
    Checks the distractor location bias and verifies the 'DistractorProb' column.
    1. Verifies the 'DistractorProb' column labels are correct against trial data.
    2. Checks the proportion of high-probability trials is as expected using a Binomial Test.
    """
    print_check_header("Distractor Bias and Probability Labeling (Statistical)")
    all_passed = True

    if 'DistractorProb' not in df.columns:
        return print_result("Distractor Checks", False, "'DistractorProb' column is missing.")

    # --- Verify label correctness ---
    labeling_errors = 0
    is_even = subject_id % 2 == 0
    biased_loc = 1 if is_even else 3

    for i, row in df.iterrows():
        is_sp = row['SingletonPresent'] == 1
        label = row['DistractorProb']
        actual_loc = row['SingletonLoc']

        if is_sp:
            expected_label = 'high-probability' if actual_loc == biased_loc else 'low-probability'
            if label != expected_label:
                labeling_errors += 1
        elif label != 'distractor-absent':
            labeling_errors += 1

    labels_ok = labeling_errors == 0
    all_passed &= print_result("Correct Labeling in 'DistractorProb' Column", labels_ok,
                               f"Found {labeling_errors} labeling errors.")

    # --- Check the statistical proportion of high-probability trials ---
    sp_trials = df[df['SingletonPresent'] == 1]
    if sp_trials.empty:
        print("No SP trials found, skipping bias proportion check.")
        return all_passed

    n_sp_trials = len(sp_trials)
    n_high_prob = (sp_trials['DistractorProb'] == 'high-probability').sum()
    expected_prop = config['trial_sequence']['hp_distractor']

    result = binomtest(k=n_high_prob, n=n_sp_trials, p=expected_prop)
    p_value_bias = result.pvalue
    bias_ok = p_value_bias >= alpha

    message = (f"Found {n_high_prob}/{n_sp_trials} high-prob trials. "
               f"p-value = {p_value_bias:.3f} for expected proportion of {expected_prop:.0%}.")
    all_passed &= print_result("High-Probability Bias Proportion", bias_ok, message)

    return all_passed


def analyze_directory_randomness(config):
    """
    Analyzes all sequences in a directory to measure their 'randomness'
    by comparing the SP/SA sequence to a random shuffle of itself.
    """
    print_check_header("Sequence Randomness Analysis (Levenshtein on SP/SA)")
    seq_dir = config['filepaths']['sequences']
    try:
        sequence_files = [f for f in os.listdir(seq_dir) if f.endswith('.csv') and f.startswith('sci-')]
    except FileNotFoundError:
        return print_result("Directory Scan", False, f"Could not find or access directory: {seq_dir}")

    if not sequence_files:
        return print_result("Directory Scan", False, f"No sequence files found in {seq_dir}")

    distances = []
    for file_name in sequence_files:
        df = pd.read_csv(os.path.join(seq_dir, file_name))
        actual_sequence_list = df['SingletonPresent'].astype(str).tolist()
        actual_sequence_str = "".join(actual_sequence_list)

        random_sequence_list = actual_sequence_list.copy()
        random.shuffle(random_sequence_list)
        random_sequence_str = "".join(random_sequence_list)

        distance = Levenshtein.distance(actual_sequence_str, random_sequence_str)
        distances.append(distance)

    if distances:
        avg_dist = sum(distances) / len(distances)
        print(f"Analyzed {len(distances)} files. Average Levenshtein distance from random: {avg_dist:.2f}")
        print("Interpretation: Measures edits to turn the generated sequence into a random shuffle.")
        print("A higher distance implies more structure from the 'max consecutive' rule.")


def analyze_inter_sequence_similarity(config):
    """Analyzes similarity between all pairs of sequences in a directory based on SP/SA order."""
    print_check_header("Inter-Sequence Similarity Analysis (Pairwise Levenshtein on SP/SA)")
    seq_dir = config['filepaths']['sequences']
    try:
        sequence_files = [f for f in os.listdir(seq_dir) if f.endswith('.csv') and f.startswith('sci-')]
    except FileNotFoundError:
        return print_result("Directory Scan", False, f"Could not find or access directory: {seq_dir}")

    if len(sequence_files) < 2:
        print("Skipping analysis: Need at least two sequence files to compare.")
        return

    sequence_strings = []
    for file_name in sequence_files:
        df = pd.read_csv(os.path.join(seq_dir, file_name))
        sequence_strings.append("".join(df['SingletonPresent'].astype(str).tolist()))

    distances = [Levenshtein.distance(s1, s2) for s1, s2 in combinations(sequence_strings, 2)]

    if distances:
        avg_dist = sum(distances) / len(distances)
        min_dist = min(distances)
        print(f"Analyzed {len(distances)} pairs. Average distance between sequences: {avg_dist:.2f} (Min: {min_dist})")
        print("Interpretation: Measures how different the SP/SA trial orders are from each other.")
        if min_dist > (len(sequence_strings[0]) * 0.1):
             print("✅ Minimum distance is high, suggesting sequences are unique.")
        else:
             print("⚠️ Minimum distance is low, suggesting some sequences may be very similar.")


def evaluate_sequence(subject_id, block, config):
    """Main evaluation function to run all checks."""
    print(f"\n--- Evaluating Sequence for Subject {subject_id}, Block {block} ---")
    file_path = os.path.join(config['filepaths']['sequences'], f"sci-{subject_id}_block_{block}.csv")

    if not os.path.exists(file_path):
        logging.error(f"Sequence file not found: {file_path}")
        return

    df = pd.read_csv(file_path)
    logging.info(f"Successfully loaded sequence file: {file_path}")

    results = [
        check_proportions_and_rules(df, config),
        check_distractor_bias_and_labels(df, subject_id, config),
        verify_priming_labels(df),
        check_trial_integrity(df)
    ]

    print("\n" + "*" * 60, "\nEVALUATION SUMMARY", "\n" + "*" * 60)
    if all(results):
        print("✅ All checks passed. The sequence meets the new constraints.")
    else:
        print("❌ Some checks failed. Please review the log above for details.")
    print("*" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate generated trial sequences based on the new GA rules.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-c", "--config", type=str, default="config.yaml", help="Path to the configuration file.")

    # Modes of operation
    parser.add_argument("-s", "--subject", type=int, help="Subject ID for single file evaluation.")
    parser.add_argument("-b", "--block", type=int, help="Block number for single file evaluation.")
    parser.add_argument("--randomness", action="store_true", help="Analyze internal structure of all sequences.")
    parser.add_argument("--similarity", action="store_true", help="Analyze similarity between all pairs of sequences.")

    args = parser.parse_args()

    try:
        with open(args.config) as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Config file not found at '{args.config}'. Aborting.")
        exit(1)

    run_single = args.subject is not None and args.block is not None
    if not any([run_single, args.randomness, args.similarity]):
        parser.print_help()
        logging.error("\nNo action specified. Please provide an evaluation mode.")
        exit(1)

    if run_single:
        evaluate_sequence(subject_id=args.subject, block=args.block, config=config)

    if args.randomness:
        analyze_directory_randomness(config)

    if args.similarity:
        analyze_inter_sequence_similarity(config)