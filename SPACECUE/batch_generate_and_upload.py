import yaml
import os
import sys
import argparse

# Ensure utils and SPACECUE are found
sys.path.append('..')
import utils.utils
utils.utils.get_input_from_dict = lambda d, **kwargs: {"subject_id": 99, "block": 0}

from SPACECUE.generate_subject_sequence import precompute_sequence
from SPACECUE import upload_to_cloudflare

def main():
    parser = argparse.ArgumentParser(description="Generate sequences for multiple subjects and upload to Cloudflare.")
    parser.add_argument("subjects", metavar="N", type=int, nargs="+",
                        help="List of subject IDs (e.g., 8 9 10)")
    parser.add_argument("--skip-sounds", action="store_true",
                        help="Skip sound generation (CSV only)")
    
    args = parser.parse_args()
    
    # Load settings
    settings_path = "config.yaml"
    with open(settings_path) as file:
        settings = yaml.safe_load(file)
        
    if "session" not in settings: settings["session"] = {}
    if "max_consecutive_trial_type_cues" not in settings["session"]:
        settings["session"]["max_consecutive_trial_type_cues"] = 5
        
    print(f"Starting sequence generation for {len(args.subjects)} subjects...")
    for sub in args.subjects:
        print(f"Generating sequences for subject {sub}...")
        precompute_sequence(subject_id=sub, block=0, settings=settings, skip_sound_generation=args.skip_sounds)
        
    print("\n--- Generation Complete ---\n")
    print("Starting Cloudflare Upload...")
    
    upload_to_cloudflare.main()
    
    print("\nAll done!")

if __name__ == "__main__":
    main()
