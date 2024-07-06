import pandas as pd
from itertools import permutations
import yaml

# load settings
settings_path = "SPACEPRIME/config.yaml"
with open(settings_path) as file:
    settings = yaml.safe_load(file)


def generate_combinations(settings, save=True):
    """Generates all combinations of digits and locations for a given configuration."""

    digits = list(range(1, settings["session"]["n_digits"] + 1))
    locations = list(range(1, settings["session"]["n_locations"] + 1))
    all_combinations = []

    for singleton_present in [1, 0]:
        for digit_perm in permutations(digits, len(locations)):
            for loc_perm in permutations(locations, len(locations)):
                combination = {
                    "SingletonPresent": singleton_present
                }

                # Assign digit and location values dynamically
                for i, (digit, loc) in enumerate(zip(digit_perm, loc_perm)):
                    if i == 0:  # Target
                        combination["TargetDigit"] = digit
                        combination["TargetLoc"] = loc
                    elif singleton_present and i == 1:  # Singleton
                        combination["SingletonDigit"] = digit
                        combination["SingletonLoc"] = loc
                    else:  # Non-singleton
                        combination[f"Non-Singleton{i}Digit"] = digit
                        combination[f"Non-Singleton{i}Loc"] = loc

                all_combinations.append(combination)
    if save:
        df = pd.DataFrame(all_combinations)
        duplicate = df.duplicated().any()
        print(f"Duplicates found: {duplicate}")
        # clean up
        df = df.fillna(0).astype(int)
        writer = f"SPACEPRIME/all_combinations_{len(locations)}_loudspeakers_{len(digits)}_digits.xlsx"
        try:
            df.to_excel(writer, index=False)
        except ValueError:
            print("Excel sheet too large. Aborting ... ")

        print(f"Number of unique conditions: {len(df)}")

    return df


if __name__ == "__main__":
    all_combinations = generate_combinations(settings)
