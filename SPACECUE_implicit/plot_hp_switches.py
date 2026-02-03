import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import yaml
import os
import numpy as np

# Define paths relative to the script location or absolute
PROJECT_PATH = "C:/Users/Max/PycharmProjects/psychopy-experiments/SPACECUE_implicit"
CONFIG_PATH = os.path.join(PROJECT_PATH, "config.yaml")

def plot_hp_switches(subject_id):
    # Load settings
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found at {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r") as f:
        settings = yaml.safe_load(f)

    sequences_path = settings["filepaths"]["sequences"]
    n_blocks = settings["session"]["n_blocks"]
    n_trials = settings["session"]["n_trials"]
    n_locations = settings["session"]["n_locations"]
    
    print(f"Loading sequences for Subject {subject_id}...")

    # Collect all blocks
    df_list = []
    for block in range(n_blocks):
        # Construct filename based on generate_subject_sequence.py output format
        file_name = f"sci-{subject_id}_block_{block}.csv"
        file_path = os.path.join(sequences_path, file_name)
        
        if os.path.exists(file_path):
            df_block = pd.read_csv(file_path)
            # Add block offset to trial index for global plotting
            df_block["Block"] = block
            df_list.append(df_block)
        else:
            print(f"Warning: File not found for block {block}: {file_path}")

    if not df_list:
        print("No data found. Please ensure you have run the generation script.")
        return

    # Concatenate all blocks
    df = pd.concat(df_list, ignore_index=True)

    # Check for the new column
    if "HP_Distractor_Loc" not in df.columns:
        print("Error: 'HP_Distractor_Loc' column missing. Please regenerate sequences with the updated logic.")
        return

    # Determine which column represents the actual distractor location
    cue_type = settings["session"]["cue"]
    if cue_type == "distractor":
        loc_col = "SingletonLoc"
    elif cue_type == "control":
        loc_col = "Non-Singleton2Loc"
    else:
        loc_col = "SingletonLoc" # Fallback

    # Filter for Singleton Present trials
    # Assuming SingletonPresent is 1 (Present) and 0 (Absent)
    if "SingletonPresent" in df.columns:
        sp_trials = df[df["SingletonPresent"] == 1].copy()
    else:
        sp_trials = df.copy()

    # --- PLOTTING ---
    plt.figure(figsize=(14, 6))
    
    # 1. Plot the HP Rule (The intended high-probability location)
    # drawstyle="steps-post" ensures the line stays flat until the change occurs
    plt.plot(df.index, df["HP_Distractor_Loc"], label="HP Rule (Intended Bias)", 
             color="#d62728", linewidth=2.5, drawstyle="steps-post", alpha=0.9)
    
    # 2. Plot Actual Distractor Locations
    # Add jitter to y-axis to visualize density
    y_jitter = np.random.uniform(-0.15, 0.15, size=len(sp_trials))
    plt.scatter(sp_trials.index, sp_trials[loc_col] + y_jitter, 
                alpha=0.3, label=f"Actual {loc_col}", color="#1f77b4", s=15, edgecolors='none')
    
    # Formatting
    plt.yticks(range(1, n_locations + 1))
    plt.xlabel("Global Trial Index")
    plt.ylabel("Location ID")
    plt.title(f"Implicit Learning Protocol: HP Distractor Switches (Subject {subject_id})")
    
    # Add Block Boundaries
    for b in range(n_blocks + 1):
        boundary = b * n_trials
        plt.axvline(x=boundary, color='gray', linestyle='--', alpha=0.5)
        if b < n_blocks:
            # Label blocks
            plt.text(boundary + (n_trials/2), n_locations + 0.2, f"Block {b}", 
                     ha='center', va='bottom', fontsize=9, color='gray')

    plt.legend(loc='center right', frameon=True)
    plt.grid(True, axis='y', linestyle=':', alpha=0.3)
    plt.ylim(0.5, n_locations + 0.5)
    plt.tight_layout()
    
    # Save and Show
    output_file = os.path.join(sequences_path, "logs", f"sci-{subject_id}_HP_switches_plot.png")
    plt.savefig(output_file, dpi=300)
    print(f"Plot saved to: {output_file}")
    plt.show()

if __name__ == "__main__":
    # Change subject_id here if needed
    plot_hp_switches(subject_id=99)