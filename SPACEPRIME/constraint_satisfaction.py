import random
from constraint import Problem
import time


def generate_trial_sequence(num_trials, num_neg_prime, num_pos_prime, num_no_prime):
    start = time.time()
    digits = [str(i) for i in range(1, 10)]  # Stimulus pool

    problem = Problem()

    # Define variables for each trial
    for i in range(num_trials):
        problem.addVariable(f"trial_{i}_speakers", [(d1, d2, d3) for d1 in digits for d2 in digits for d3 in digits if d1 != d2 and d1 != d3 and d2 != d3])
        problem.addVariable(f"trial_{i}_type", ["neg_prime", "pos_prime", "no_prime"])

    # Constraint: no more than two consecutive trials with the same prime type
    for i in range(num_trials - 2):
        problem.addConstraint(lambda t1, t2, t3: t1 != t2 or t2 != t3,
                              (f"trial_{i}_type", f"trial_{i+1}_type", f"trial_{i+2}_type"))

    # Constraint: equal number of trials per condition
    problem.addConstraint(lambda *types: types.count("neg_prime") >= num_neg_prime,
                          [f"trial_{i}_type" for i in range(num_trials)])
    problem.addConstraint(lambda *types: types.count("pos_prime") >= num_pos_prime,
                          [f"trial_{i}_type" for i in range(num_trials)])
    problem.addConstraint(lambda *types: types.count("no_prime") >= num_no_prime,
                          [f"trial_{i}_type" for i in range(num_trials)])

    solutions = problem.getSolutions()

    if solutions:
        # Choose a random solution and extract trial details
        solution = random.choice(solutions)
        trial_sequence = []
        for i in range(num_trials):
            speakers = solution[f"trial_{i}_speakers"]
            trial_type = solution[f"trial_{i}_type"]
            trial_sequence.append((speakers, trial_type))  # Store speaker assignment and trial type
        print(f"Time needed: {time.time() - start}")
        return trial_sequence
    else:
        print(f"Time needed: {time.time() - start}")
        return None


trial_sequence = generate_trial_sequence(2000, 10, 10, 10)

if trial_sequence:
    print("Trial sequence generated successfully:")
    for i, (speakers, trial_type) in enumerate(trial_sequence):
        print(f"Trial {i+1}: Speakers: {speakers}, Type: {trial_type}")
else:
    print("No valid trial sequence found.")
