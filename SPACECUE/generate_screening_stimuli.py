import os
import glob
import slab
import yaml
from utils.signal_processing import spatialize
from SPACECUE.encoding import SPACE_ENCODER

def main():
    # Load config to get the correct level
    with open("config.yaml", "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    soundlvl = settings["session"]["level"]
    stimuli_dir = "stimuli/digits_all_250ms"
    output_dir = "screening_stimuli"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Find all wav files in the stimuli directory
    stim_files = glob.glob(os.path.join(stimuli_dir, "*.wav"))
    
    if not stim_files:
        print(f"No .wav files found in {stimuli_dir}")
        return
        
    for stim_file in stim_files:
        basename = os.path.basename(stim_file)
        digit_name = os.path.splitext(basename)[0] # e.g. "1" or "2"
        
        # Load the sound using slab
        try:
            sound = slab.Sound(stim_file)
            sound.level = soundlvl  # MATCH THE EXPERIMENT LEVEL
        except Exception as e:
            print(f"Error loading {stim_file}: {e}")
            continue
            
        # Render for each location in SPACE_ENCODER
        for loc_id, (azi, ele) in SPACE_ENCODER.items():
            # loc_id: 1, 2, 3
            # azi: -90, 0, 90
            try:
                rendered_sound = spatialize(sound, azi=azi, ele=ele)
                out_filename = f"{digit_name}_loc{loc_id}.wav"
                out_path = os.path.join(output_dir, out_filename)
                rendered_sound.write(out_path, normalise=False)
                print(f"Saved {out_path}")
            except Exception as e:
                print(f"Error rendering {digit_name} at loc {loc_id}: {e}")

if __name__ == "__main__":
    main()
