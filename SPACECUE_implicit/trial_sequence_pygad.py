import pygad
import matplotlib.pyplot as plt
import numpy as np
import random
from collections import Counter
import seaborn as sns
import logging
import heapq


def make_pygad_trial_sequence(fig_path=None, num_trials=225, conditions=(1, 2, 3), prop_c=0.6, prop_np=0.2, prop_pp=0.2,
                              rule_violation_factor=1000, num_generations=3000, num_parents_mating=10,
                              sol_per_pop=200, keep_parents=2, mutation_percent_genes=5,
                              fitness_threshold=0.9999):
    # Define Trial Parameters
    desired_c = prop_c * num_trials
    desired_np = prop_np * num_trials
    desired_pp = prop_pp * num_trials
    max_np_pp = int(num_trials * prop_np) + int(num_trials * prop_pp)
    max_fitness = 0  # Since we're only using penalties, the ideal fitness is 0
    max_violation_count = max_np_pp // 2 - 1
    min_fitness = - 2 * (max_violation_count * rule_violation_factor) - num_trials * (2 - 2*prop_c)

    # Fitness Function
    def fitness_func(ga_instance, solution, solution_idx):
        fitness = 0
        # Convert integers to condition labels for easier comparison
        solution_labels = ["C" if x == 1 else "NP" if x == 2 else "PP" for x in solution]  # 1 C, 2 NP, 3 PP

        # 1. Desired proportion of conditions
        counts = Counter(solution_labels)
        count_penalty = abs(desired_c - counts.get("C", 0)) + \
                        abs(desired_pp - counts.get("PP", 0)) + \
                        abs(desired_np - counts.get("NP", 0))
        fitness -= count_penalty

        # 2. At Least One C Between NP and PP
        violation_count = 0
        for i in range(len(solution_labels) - 1):
            if solution_labels[i] in ("NP", "PP") and solution_labels[i + 1] in ("NP", "PP"):
                violation_count += 1
        fitness -= violation_count * rule_violation_factor

        # 3. Solution must start with C
        if solution_labels[0] != "C":
            # Apply a fixed, large penalty if the first element is not 'C'
            fitness -= rule_violation_factor

        # Avoid division by zero if max_fitness equals min_fitness
        if max_fitness == min_fitness:
            return 0.0

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
                           gene_space=list(conditions),
                           gene_type=int,
                           parent_selection_type="sss",
                           keep_parents=keep_parents,
                           mutation_type="random",
                           mutation_percent_genes=mutation_percent_genes,
                           suppress_warnings=True,
                           on_generation=on_generation) # Stop based on fitness

    ga_instance.run()

    # Get the Best Solution
    solution, solution_fitness, solution_idx = ga_instance.best_solution()
    logging.info(f"GA finished after {ga_instance.generations_completed} generations.")
    logging.info(f"Fitness value of the best solution = {solution_fitness}")
    logging.info(f"TRAITS OF FITTEST TRIAL SEQUENCE: \n"
                 f"Control trials: {solution.tolist().count(1)} \n"
                 f"Negative priming trials: {solution.tolist().count(2)} \n"
                 f"Positive priming trials: {solution.tolist().count(3)} ")
    sequence_labels = ["C" if x == 1 else "NP" if x == 2 else "PP" for x in solution]

    if fig_path:
        #ga_instance.plot_fitness(save_dir=fig_path,
        #                         title=f"Trial sequence fitness: {round(solution_fitness, 5)}",
        #                         color="black")
        #plt.close()
        pass
    return solution, sequence_labels, solution_fitness


def insert_singleton_present_trials(sequence, fig_path=None):
    while True:
        copy = sequence.copy()
        # Calculate the desired number of "SingletonPresent" == 1 trials
        target_singleton_present_trials = len(copy) // 2
        current_singleton_present_trials = 0
        occupied_suffix_indices = list()
        # iterate over sequence
        for i, element in enumerate(copy):
            if i < len(copy) - 1:
                upcoming_element = copy[i+1]
            else:
                upcoming_element = None
            if upcoming_element == "NP" and element == "C":
                copy[i] += "_SP"
                current_singleton_present_trials += 1
                occupied_suffix_indices.append(i)
        remaining_singleton_present_trials = target_singleton_present_trials - current_singleton_present_trials
        all_indices = list(range(len(copy)))
        remaining_indices = list(set(all_indices) - set(occupied_suffix_indices))
        random_suffix_selection = random.sample(remaining_indices, remaining_singleton_present_trials)
        for i, element in enumerate(copy):
            if i in random_suffix_selection:
                copy[i] += "_SP"
        sp_indices = get_element_indices(copy, element="SP")
        distances_sp = np.diff(sp_indices)
        occurrences = Counter(distances_sp)
        top_three_keys = heapq.nlargest(3, occurrences, key=occurrences.get)
        if occurrences[top_three_keys[0]] < occurrences[top_three_keys[1]] + occurrences[top_three_keys[2]]:
            logging.info(f"Found the following occurrences of sp distances: {list(occurrences.items())}.")
            break
        else:
            continue
    if fig_path:
        # plot the stuff
        sns.histplot(data=distances_sp)
        plt.title("Histogram of distances between SP trials")
        plt.savefig(fig_path)
        plt.close()
    return copy


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
                 f"Control trials: {c_count} \n"
                 f"Negative priming trials: {np_count} \n"
                 f"Positive priming trials: {pp_count} \n"
                 f"Attended repetition control trials: {attended_rc} \n"
                 f"Ignored repetition control trials: {ignored_rc} ")


if __name__ == "__main__":
    solution, solution_fitness = make_pygad_trial_sequence()
    # Example usage
    original_sequence = solution  # Your provided sequence
    modified_sequence = insert_singleton_present_trials(original_sequence)
    print(modified_sequence)

