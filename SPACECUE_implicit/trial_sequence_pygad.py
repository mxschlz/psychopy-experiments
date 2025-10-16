import pygad
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import seaborn as sns
import logging


def make_pygad_trial_sequence(fig_path=None, num_trials=225, prop_sp=0.7,
                              rule_violation_factor=1000, num_generations=3000, num_parents_mating=10,
                              sol_per_pop=200, keep_parents=2, mutation_percent_genes=5,
                              fitness_threshold=0.9999):
    """
    Generates a trial sequence using a genetic algorithm.

    The sequence consists of two types of trials, represented by integers in the GA:
    - 1: Singleton Present (SP)
    - 0: Singleton Absent (SA)

    The GA optimizes for two criteria:
    1. The proportion of SP trials should match `prop_sp`.
    2. There should be a maximum of 5 consecutive SP trials.
    """
    # Define Trial Parameters
    gene_space = [0, 1]  # 0 for Singleton Absent, 1 for Singleton Present
    desired_sp = prop_sp * num_trials
    desired_sa = (1 - prop_sp) * num_trials

    # Since we only use penalties, the ideal fitness is 0.
    # We normalize it to be between 0 and 1 for the GA's `on_generation` callback.
    max_fitness = 0
    # Estimate a reasonable minimum fitness for normalization.
    # Worst case: all trials are of one type (penalty ~num_trials) and a rule is violated (penalty ~rule_violation_factor)
    min_fitness = -num_trials - rule_violation_factor

    # Fitness Function
    def fitness_func(ga_instance, solution, solution_idx):
        fitness = 0

        # 1. Desired proportion of SP/SA trials
        counts = Counter(solution)
        count_penalty = abs(desired_sp - counts.get(1, 0)) + \
                        abs(desired_sa - counts.get(0, 0))
        fitness -= count_penalty

        # 2. Penalize sequences with more than 5 consecutive SP trials
        max_consecutive_sp_allowed = 5
        consecutive_sp_count = 0
        for trial in solution:
            if trial == 1:
                consecutive_sp_count += 1
                if consecutive_sp_count > max_consecutive_sp_allowed:
                    fitness -= rule_violation_factor
                    break  # Rule is violated, no need to check further
            else:
                # Reset counter if the trial is not an SP trial
                consecutive_sp_count = 0

        # Avoid division by zero if max_fitness equals min_fitness
        if max_fitness == min_fitness:
            return 0.0

        # Normalize fitness to be in the range [0, 1] for the threshold check
        normalized_fitness = (fitness - min_fitness) / (max_fitness - min_fitness)
        return normalized_fitness

    # Callback function to stop GA when fitness threshold is reached
    def on_generation(ga_instance):
        best_fitness = ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]
        if best_fitness >= fitness_threshold:
            logging.info(f"Fitness threshold of {fitness_threshold} reached. Stopping at generation {ga_instance.generations_completed}.")
            return "stop"

    # GA Parameters
    ga_instance = pygad.GA(num_generations=num_generations,
                           num_parents_mating=num_parents_mating,
                           fitness_func=fitness_func,
                           sol_per_pop=sol_per_pop,
                           num_genes=num_trials,
                           gene_space=gene_space,
                           gene_type=int,
                           parent_selection_type="sss",
                           keep_parents=keep_parents,
                           mutation_type="random",
                           mutation_percent_genes=mutation_percent_genes,
                           suppress_warnings=True,
                           on_generation=on_generation)

    ga_instance.run()

    # Get the Best Solution
    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    logging.info(f"GA finished after {ga_instance.generations_completed} generations.")
    logging.info(f"Fitness value of the best solution = {solution_fitness}")

    # The base trial type is always 'Control'. Priming is not an enforced factor.
    # We label trials based on whether a singleton is present or not.
    sequence_labels = ["C_SP" if x == 1 else "C" for x in solution]

    counts = Counter(sequence_labels)
    logging.info(f"TRAITS OF FITTEST TRIAL SEQUENCE: \n"
                 f"Singleton Present trials: {counts.get('C_SP', 0)} \n"
                 f"Singleton Absent trials: {counts.get('C', 0)}")

    if fig_path:
        # Optional: Plot distribution of distances between SP trials for the best solution
        sp_indices = [i for i, trial in enumerate(solution) if trial == 1]
        if len(sp_indices) > 1:
            plt.figure()
            sns.histplot(data=np.diff(sp_indices))
            plt.title("Histogram of distances between SP trials in best solution")
            plt.xlabel("Trials between SP trials")
            plt.ylabel("Frequency")
            plt.savefig(fig_path)
            plt.close()

    # Return the labels and fitness. The labels are what the downstream script will use.
    return sequence_labels, solution_fitness


def get_element_indices(sequence, element):
    return [i for i, trial in enumerate(sequence) if element in trial]


def print_final_traits(dataframe):
    sp_count = 0
    c_count = dataframe["Priming"].tolist().count(0)
    np_count = dataframe["Priming"].tolist().count(-1)
    pp_count = dataframe["Priming"].tolist().count(1)
    ignored_rc = 0
    attended_rc = 0
    total_length = 0
    prev_target_digit = None
    prev_singleton_digit = None
    prev_target_loc = None
    prev_singleton_loc = None
    for i, sample in dataframe.iterrows():
        total_length += 1
        if sample["SingletonPresent"]:
            sp_count += 1
        if (
            sample["SingletonDigit"] == prev_target_digit
            and sample["SingletonLoc"] == prev_target_loc
        ):
            attended_rc += 1
        if (
            sample["SingletonDigit"] == prev_singleton_digit
            and sample["SingletonLoc"] == prev_singleton_loc
        ):
            ignored_rc += 1
        # Update the previous trial's values
        prev_target_digit = sample["TargetDigit"]
        prev_singleton_digit = sample["SingletonDigit"]
        prev_target_loc = sample["TargetLoc"]
        prev_singleton_loc = sample["SingletonLoc"]

    logging.info(f"THE FINAL TRIAL SEQUENCE CONTAINS: \n"
                 f"Total length of sequence: {total_length} \n"
                 f"Singleton present trials: {sp_count} \n"
                 f"Control trials (by random chance): {c_count} \n"
                 f"Negative priming trials (by random chance): {np_count} \n"
                 f"Positive priming trials (by random chance): {pp_count} \n"
                 f"Attended repetition control trials: {attended_rc} \n"
                 f"Ignored repetition control trials: {ignored_rc} ")


if __name__ == "__main__":
    # Example usage of the new function
    final_sequence_labels, fitness = make_pygad_trial_sequence(num_trials=225, prop_sp=0.7)
    print(f"Generated a sequence of {len(final_sequence_labels)} trials with fitness {fitness:.4f}")
    print(f"First 20 trials: {final_sequence_labels[:20]}")
    print(f"SP count: {final_sequence_labels.count('C_SP')}")