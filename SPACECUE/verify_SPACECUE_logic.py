# test_cues_and_stimuli.py
# Place this script inside your SPACECUE directory.
# Ensure config.yaml has fullscr: false for easier testing.

import os
import sys
import pandas as pd
from psychopy import core  # visual is implicitly used by Session
import time

# Ensure the project root (e.g., 'psychopy-experiments') is in sys.path
# to allow imports like 'from utils.sound import ...'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added to sys.path: {project_root}")

# Set ASIO environment variable (as in your original script)
os.environ["SD_ENABLE_ASIO"] = "1"

# Project-specific imports
try:
    from SPACECUE.experiment_logic import SpaceCueSession
except ImportError as e:
    print(f"Failed to import SpaceCueSession: {e}")
    print("Make sure this script is in the SPACECUE directory and SPACECUE/experiment_logic.py exists.")
    sys.exit(1)

# --- Configuration for the Test ---
SETTINGS_FILE = "config.yaml"  # Assumed to be in the SPACECUE directory
OUTPUT_DIR = "logs"  # Temporary directory for any logs this test session might create
SUBJECT_ID_STR = "sub-01"  # Dummy subject ID for this test session
BLOCK_TO_TEST = 1  # Which block number to test (1-indexed)


def main():
    # Ensure Current Working Directory (CWD) is the script's directory (SPACECUE)
    # This helps with relative paths in config.yaml and for loading stimuli/sequences.
    expected_cwd = os.path.dirname(os.path.abspath(__file__))
    if os.getcwd() != expected_cwd:
        print(f"Changing CWD from '{os.getcwd()}' to script directory: '{expected_cwd}'")
        os.chdir(expected_cwd)
    else:
        print(f"CWD is already script directory: {expected_cwd}")

    # Check for essential configuration file
    if not os.path.exists(SETTINGS_FILE):
        print(f"Error: Settings file '{SETTINGS_FILE}' not found in {os.getcwd()}.")
        print(f"Please ensure '{SETTINGS_FILE}' is present in the SPACECUE directory.")
        return

    session = None  # Initialize for the finally block

    try:
        # 1. Initialize SpaceCueSession.
        #    It will create its own PsychoPy window based on settings in config.yaml.
        print(f"Initializing SpaceCueSession (Subject: {SUBJECT_ID_STR}, Output Dir: {OUTPUT_DIR})...")
        session = SpaceCueSession(
            output_str=SUBJECT_ID_STR,
            output_dir=OUTPUT_DIR,
            settings_file=SETTINGS_FILE,
            test=True  # The 'test' flag in your SpaceCueSession might alter some behaviors (e.g., skip prompts)
        )
        print("SpaceCueSession initialized.")

        # Ensure the output directory for logs exists (session might create it, but good to be sure)
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            print(f"Created output directory: {OUTPUT_DIR}")

        # 2. Load the specified block and create trials
        print(f"\n--- Setting up Block {BLOCK_TO_TEST} ---")
        # Your set_block method seems to use a 1-indexed block number.
        session.set_block(block=BLOCK_TO_TEST)
        print(f"Block set. Sequence directory: {session.blockdir}")

        print(f"Loading sequence file: {session.blockdir + '.csv'}")
        session.load_sequence()

        if not isinstance(session.sequence, pd.DataFrame) or session.sequence.empty:
            print(
                f"Error: Sequence for block {BLOCK_TO_TEST} (expected file: {session.blockdir + '.csv'}) is empty or failed to load.")
            print("Please check your sequence files, paths, and subject ID configuration.")
            return
        print(f"Sequence loaded with {len(session.sequence)} trials.")

        # Durations for trial creation.
        # SpaceCueTrial's __init__ will use some of these values and overwrite
        # ITI and cue_stim_delay from the loaded sequence data.
        # We need to provide a tuple/list of the correct length (5 phases).
        trial_durations = (
            session.settings["session"]["cue_duration"],
            None,  # Placeholder for cue_stim_delay_jitter (will be overwritten by trial)
            session.settings["session"]["stimulus_duration"],
            session.settings["session"]["response_duration"],
            None  # Placeholder for ITI-Jitter (will be overwritten by trial)
        )

        print(f"Creating {len(session.sequence)} trials for the block...")
        session.create_trials(
            n_trials=len(session.sequence),
            durations=trial_durations,
            timing=session.settings["session"]["timing"]
        )

        if not session.trials:
            print("Error: No trials were created. Exiting.")
            return
        print(f"{len(session.trials)} trials created successfully.")

        # 3. Iterate through trials for testing
        for trial_idx, current_trial in enumerate(session.trials):
            print(f"\n--- Testing Trial (Sequence Trial Nr: {current_trial.trial_nr}, List Index: {trial_idx}) ---")

            # Print trial information
            print("  Trial Parameters:")
            for key, value in current_trial.parameters.items():
                print(f"    {key}: {value}")
            print(f"  Calculated Trigger Name: {current_trial.trigger_name}")
            if current_trial.stim and hasattr(current_trial.stim, 'filename'):
                print(f"  Stimulus file: {os.path.basename(current_trial.stim.filename)}")
            else:
                print("  Stimulus file: No stimulus loaded or filename attribute missing")
            print(f"  Phase durations for this trial: {current_trial.phase_durations}")

            # Display the cue
            # The display_cue_interval method (which you recently updated with print statements)
            # uses self.session.arrows and self.session.sequence.iloc[self.trial_nr].
            print("  Displaying cue (see subsequent prints from display_cue_interval)...")
            current_trial.display_cue_interval()
            session.win.flip()  # Show the cue on screen
            print("  Cue displayed on screen.")

            # Play the stimulus sound
            if current_trial.stim:
                print(f"  Playing stimulus sound (includes 80ms wait & trigger print from send_trig_and_sound)...")
                current_trial.send_trig_and_sound()  # This method plays sound, waits 80ms, and prints trigger info
            else:
                print("  No stimulus sound to play for this trial. Waiting for 1 sec...")
                core.wait(1.0)  # Wait a bit if no sound, to simulate trial time

            # Wait for user input to proceed
            time.sleep(5)

        print("\n--- Test Iteration Finished ---")

    except Exception as e:
        print(f"\nAN UNEXPECTED ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 4. Cleanup
        if session and hasattr(session, 'win') and session.win:
            print("Closing PsychoPy window...")
            session.win.close()
        print("Quitting PsychoPy core...")
        core.quit()
        print("Test script finished.")


if __name__ == "__main__":
    main()
