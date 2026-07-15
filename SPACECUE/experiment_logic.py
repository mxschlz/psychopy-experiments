import psychopy.visual

from utils.set_logging_level import set_level
from exptools2.core import Trial, Session
from exptools2.stimuli import create_shape_stims
import os
os.environ["SD_ENABLE_ASIO"] = "1"
import SPACECUE.prompts as prompts
import pandas as pd
from utils.sound import SoundDeviceSound as Sound
from psychopy import parallel, core, event
import random
import numpy as np
from SPACECUE.encoding import *
import csv


class SpaceCueTrial(Trial):
    def __init__(self, session, trial_nr, phase_durations, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.stim = None
        # HACKY AND NOT RECOMMENDED --> special case to implement ITI jitter
        # add ITI jitter to the trial
        # self.phase_names.append("iti")
        self.phase_durations[-1] = self.session.sequence["ITI-Jitter"].iloc[trial_nr]
        self.phase_durations[1] = self.session.sequence["cue_stim_delay_jitter"].iloc[trial_nr]
        self.trigger_name = None  # this holds the trial-specific trigger name encoding

        # Initialize response-related flags
        self._response_recorded = False
        self._clicked_on_target_for_response = False # True if the recorded response was on a valid target area

    def send_trig_and_sound(self):
        self.stim.play(latency="low", blocksize=0)  # not sure whether this does anything ...
        self.wait(delay_ms=80)  # wait for 80 ms because of constant internal delay
        self.session.send_trigger(trigger_name=self.trigger_name)

    def draw(self):
        # Track the mouse position (e.g., for checking if it's over the box) IN EVERY PHASE
        self.track_mouse_pos()  # Assuming this method updates mouse-related state

        # --- Phase 0: Display the cue ---
        if self.phase == 0:
            self.session.default_fix.draw()
            self.display_cue_interval()

        # --- Phase 1: Wait period / Display default fixation ---
        elif self.phase == 1:  # Changed to elif for clarity if phases are mutually exclusive per frame
            self.session.default_fix.draw()

        # --- Phases 2 and onwards: Stimulus presentation, response, feedback, etc. ---
        elif self.phase >= 2:  # Changed to elif
            if self.session.response_device == "mouse":
                # Draw the virtual response box if it exists
                if hasattr(self.session, 'virtual_response_box') and self.session.virtual_response_box:
                    self.session.display_response_box()

                # Updated mouse visibility logic:
                # Visible if no response recorded yet, OR if response was recorded but not on a target.
                # Hidden if response was recorded AND it was on a target.
                hide_cursor = self._response_recorded and self._clicked_on_target_for_response
                self.session.mouse.setVisible(not hide_cursor)

            # If using a keypad and fixation is needed during response phases, draw it.
            elif self.session.response_device == "keypad":  # Changed to elif
                self.session.default_fix.draw()  # Draw fixation

            # --- Logic specific to the *start* of Phase 2 ---
            if self.phase == 2 and (not hasattr(self, '_phase2_setup_done') or not self._phase2_setup_done):
                self._phase2_setup_done = True

                if self.session.response_device == "mouse":
                    if hasattr(self.session, 'virtual_response_box') and self.session.virtual_response_box:
                        if self.session.virtual_response_box:  # Ensure list is not empty before indexing
                            self.session.virtual_response_box[0].lineColor = "black"
                    self.session.mouse.setPos((0, 0))  # Reset mouse position

                # Stimulus presentation trigger (assuming the stimulus starts at phase 2)
                if not hasattr(self, '_stim_triggered') or not self._stim_triggered:
                    self.send_trig_and_sound()
                    self._stim_triggered = True

            # --- Response handling in Phase 3 (main response window) ---
            # Check for mouse press response if using mouse and no response yet recorded
            if self.phase == 3 and not self._response_recorded:
                if self.session.response_device == "mouse":
                    # mouse.getPressed() returns ([L,M,R buttons], [L,M,R press times]) if getTime=True
                    # We check if any button in the first list element (buttons) is pressed.
                    buttons_pressed, _ = self.session.mouse.getPressed(getTime=True)
                    if any(buttons_pressed):
                        clicked_on_target_area = False
                        if hasattr(self.session, 'virtual_response_box') and self.session.virtual_response_box:
                            for stim_in_box in self.session.virtual_response_box:
                                if stim_in_box.contains(self.session.mouse):
                                    clicked_on_target_area = True
                                    break

                        if clicked_on_target_area:
                            self._response_recorded = True
                            self._clicked_on_target_for_response = True
                            # Mouse visibility is handled by the general logic at the start of this phase block
                        else:
                            # Clicked, but not on a designated target area ("digit").
                            # In phase 3, an off-target click is NOT recorded as a response.
                            # _response_recorded remains False. Cursor remains visible (due to general logic).
                            pass

                            # --- Phase 4: Post-response or Timeout handling ---
        if self.phase == 4:  # This should be independent of the previous elif self.phase >= 2
            # Stop stimulus when entering phase 4
            if hasattr(self, '_stim_triggered') and self._stim_triggered:
                if hasattr(self.stim, 'is_playing') and callable(self.stim.is_playing):  # Robust check
                    if self.stim.is_playing():
                        self.stim.stop()

            response_detected_in_phase_4 = False  # Flag for any click occurring in phase 4
            if self.session.response_device == "mouse":
                buttons_pressed_phase4, _ = self.session.mouse.getPressed(getTime=True)
                if any(buttons_pressed_phase4):
                    response_detected_in_phase_4 = True

                    # If no response was recorded in phase 3, this is the first (late) response
                    if not self._response_recorded:
                        self._response_recorded = True  # A response (late) is now being recorded

                        clicked_on_target_area_late = False
                        if hasattr(self.session, 'virtual_response_box') and self.session.virtual_response_box:
                            for stim_in_box in self.session.virtual_response_box:
                                if stim_in_box.contains(self.session.mouse):
                                    clicked_on_target_area_late = True
                                    break

                        if clicked_on_target_area_late:
                            self._clicked_on_target_for_response = True
                            print("Late mouse response (on target area) recorded in phase 4")
                        else:
                            self._clicked_on_target_for_response = False  # Clicked off-target
                            print("Late mouse response (not on target area, but recorded) in phase 4")

            # Change box color to red for late response feedback if any click occurred in phase 4
            if response_detected_in_phase_4:
                if hasattr(self.session, 'virtual_response_box') and self.session.virtual_response_box:
                    if self.session.virtual_response_box:  # Ensure list is not empty
                        self.session.virtual_response_box[0].lineColor = "darkorange"

    def display_cue_interval(self):
        # --- 1. Get trial information ---
        # Access data from the current trial's data handler
        # Using .get() is good practice for robustness if a column might be missing
        cue_color_str = self.session.sequence.iloc[self.trial_nr].get("Color",
                                                                      "target-white-distractor-white")  # Provide a default
        cue_instruction = self.session.sequence.iloc[self.trial_nr].get("CueInstruction",
                                                                        "cue_neutral")  # Provide a default
        target_loc_raw = self.session.sequence.iloc[self.trial_nr].get("TargetLoc")
        singleton_loc_raw = self.session.sequence.iloc[self.trial_nr].get("SingletonLoc")

        # --- 2. Parse the color string and define neutral color ---
        target_color = 'white'  # Default
        distractor_color = 'white'  # Default
        neutral_color = 'white'  # Color for non-highlighted arrows

        try:
            color_parts = cue_color_str.split('-')
            if 'target' in color_parts:
                try:
                    target_index = color_parts.index('target')
                    if target_index + 1 < len(color_parts):  # Check if color name exists
                        target_color = color_parts[target_index + 1]
                    else:
                        print(f"    Warning: Target color name missing after 'target' in '{cue_color_str}'.")
                except (ValueError, IndexError):  # Catch if 'target' not found or index out of bounds
                    print(f"    Warning: Could not parse target color from '{cue_color_str}'.")

            if 'distractor' in color_parts:
                try:
                    distractor_index = color_parts.index('distractor')
                    if distractor_index + 1 < len(color_parts):  # Check if color name exists
                        distractor_color = color_parts[distractor_index + 1]
                    else:
                        print(f"    Warning: Distractor color name missing after 'distractor' in '{cue_color_str}'.")
                except (ValueError, IndexError):  # Catch if 'distractor' not found or index out of bounds
                    print(f"    Warning: Could not parse distractor color from '{cue_color_str}'.")
        except Exception as e:
            print(f"    Error parsing color string '{cue_color_str}': {e}. Using default colors.")
            target_color = 'white'
            distractor_color = 'white'

        # --- 3. Determine the cued location index and cue type ---
        cued_index = None  # Index of the arrow to be cued (0=left, 1=up, 2=right)
        cue_type = 'neutral'  # Overall type of cueing for this trial

        if "cue_nonsingleton_location" in cue_instruction:
            cue_type = 'nonsingleton'
            nonsingleton_loc_raw = self.session.sequence.iloc[self.trial_nr].get("Non-Singleton2Loc")
            if nonsingleton_loc_raw is not None:
                try:
                    cued_index = int(nonsingleton_loc_raw) - 1  # Explicitly convert to int
                except (ValueError, TypeError):
                    print(
                        f"    WARNING: Could not convert Non-Singleton2Loc '{nonsingleton_loc_raw}' to int. Cueing might be incorrect.")
                    cued_index = None  # Invalidate if conversion fails
            else:
                print(f"    WARNING: Non-Singleton2Loc is None for a 'cue_nonsingleton_location' instruction.")
        elif "cue_distractor_location" in cue_instruction:
            cue_type = 'distractor'
            if singleton_loc_raw is not None:
                try:
                    cued_index = int(singleton_loc_raw) - 1  # Explicitly convert to int
                except (ValueError, TypeError):
                    print(
                        f"    WARNING: Could not convert SingletonLoc '{singleton_loc_raw}' to int. Cueing might be incorrect.")
                    cued_index = None  # Invalidate if conversion fails
            else:
                print(f"    WARNING: SingletonLoc is None for a 'cue_distractor_location' instruction.")

        # --- 4. Set colors, draw all arrows, and display ---
        if not hasattr(self.session, 'arrows') or not isinstance(self.session.arrows, (list, tuple)) or len(
                self.session.arrows) < 3:
            print("  ERROR: self.session.arrows is not a list/tuple containing at least 3 arrow stimulus objects.")
            return

        for i, arrow in enumerate(self.session.arrows):
            current_arrow_color = neutral_color  # Default to neutral

            if cue_type == 'neutral':
                current_arrow_color = neutral_color
            elif cue_type in ['nonsingleton', 'distractor']:
                # Only color if cued_index is valid and matches the current arrow's index
                if cued_index is not None and i == cued_index:
                    if cue_type == 'nonsingleton':
                        current_arrow_color = target_color
                    else:  # cue_type is 'distractor'
                        current_arrow_color = distractor_color

            arrow.setFillColor(current_arrow_color)
            arrow.setLineColor(current_arrow_color)
            arrow.draw()

class SpaceCueSession(Session):
    def __init__(self, output_str, output_dir=None, settings_file=None, starting_block=0, test=False, demographics=None):
        if not isinstance(output_str, str):
            print(f"output_str must be of type str, got {type(output_str)}")
            output_str = str(output_str)
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file)
        self.demographics = demographics if demographics is not None else {}
        self.blocks = range(starting_block, self.settings["session"]["n_blocks"])
        self.n_trials = self.settings["session"]["n_trials"]
        self.blockdir = str
        self.sequence = pd.DataFrame
        self.logger = set_level(self.settings["logging"]["level"])
        self.test = test
        self.this_block = None
        self.subject_id = int(self.output_str.split("-")[1])
        self.subj_id_is_even = True if self.subject_id % 2 == 0 else False
        self.targets = [Sound(filename=os.path.join("../SPACECUE/stimuli/targets_low_30_Hz", x),
                              device=self.settings["soundconfig"]["device"],
                              mul=self.settings["soundconfig"]["mul"]) for x in
                        os.listdir(f"../SPACECUE/stimuli/targets_low_30_Hz")]
        self.controls = [Sound(filename=os.path.join("../SPACECUE/stimuli/digits_all_250ms", x),
                               device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"]) for x in
                         os.listdir(f"../SPACECUE/stimuli/digits_all_250ms")]
        if self.settings["mode"]["record_eeg"]:
            self.port = parallel.ParallelPort(0xCFF8)  # set address of port
        self.arrows = create_shape_stims(self.win, arrow_size=self.settings["session"]["arrow_size"],
                                         arrow_offset=self.settings["session"]["arrow_offset"])

    def display_response_box(self):
        for stimulus in self.virtual_response_box:
            stimulus.draw()

    def set_block(self, block):
        self.blockdir = os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_{block}")
        self.display_text(text=f"Initialisiere Block {block+1} von insgesamt {max(self.blocks)+1}... ",
                          duration=3.0)
        self.this_block = block

    def load_sequence(self):
        self.sequence = pd.read_csv(self.blockdir + ".csv")

    def create_trials(self, n_trials, durations, timing="seconds"):
        self.trials = []
        for trial_nr in range(n_trials):
            trial_params = dict(self.sequence.iloc[trial_nr],
                                block=self.this_block,
                                subject_id=self.subject_id)
            if self.demographics:
                trial_params.update(self.demographics)
                
            trial = SpaceCueTrial(session=self,
                                    trial_nr=trial_nr,
                                    phase_durations=durations,
                                    phase_names=["cue", "cue_stim_delay", "stim", "response", "iti"],
                                    parameters=trial_params,
                                    verbose=True,
                                    timing=timing,
                                    draw_each_frame=True)
            sound_path = os.path.join(trial.session.blockdir, f"s_{trial.trial_nr}.wav")  # s_0, s_1, ... .wav
            trial.stim = Sound(filename=sound_path, device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"])
            trial.trigger_name = f'Target-{int(trial.parameters["TargetLoc"])}-Singleton-{int(trial.parameters["SingletonLoc"])}-{PRIMING[trial.parameters["Priming"]]}'
            self.trials.append(trial)

    def run(self, starting_block):
        # self.send_trigger("experiment_onset")  # We do not need this since this was not recorded in SPACEPRIME, anyway.
        # --- STUDY INFO & CONSENT ---
        if starting_block == 0:
            from psychopy import event, core
            from psychopy.visual import TextStim
            
            idx = 0
            while idx < len(prompts.info_pages):
                page_text = prompts.info_pages[idx]
                nav_hint = "\n\n[Rechte Pfeiltaste = Weiter"
                if idx > 0:
                    nav_hint += " | Linke Pfeiltaste = Zurück]"
                else:
                    nav_hint += "]"
                    
                text_stim = TextStim(self.win, text=page_text.replace("[Drücken Sie LEERTASTE, um weiterzublättern]", "") + nav_hint, height=0.5, wrapWidth=30)
                text_stim.draw()
                self.win.flip()
                
                keys = event.waitKeys(keyList=["right", "left"])
                if "right" in keys:
                    idx += 1
                elif "left" in keys and idx > 0:
                    idx -= 1
            text_stim = TextStim(self.win, text=prompts.consent_form, height=0.5, wrapWidth=30)
            text_stim.draw()
            self.win.flip()
            keys = event.waitKeys(keyList=["j", "n"])
            if "n" in keys:
                import glob
                import os
                
                # If they say no, make sure we completely wipe any logs or data created so far for this run
                log_dir = self.settings.get("filepaths", {}).get("logs", "logs")
                data_dir = self.settings.get("filepaths", {}).get("data", "data")
                
                created_files = glob.glob(os.path.join(log_dir, f"*{self.output_str}*")) + \
                                glob.glob(os.path.join(data_dir, f"*{self.output_str}*"))
                                
                for file_path in created_files:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                
                core.quit()
                
            # --- Headphone & Volume Check ---
            test_sound_path = os.path.join(self.blockdir, "s_0.wav")
            test_sound = Sound(filename=test_sound_path, device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"])
            headphone_text = """
Kopfhörer-Test & Lautstärke

Dieses Experiment erfordert das Tragen von Kopfhörern. Bitte stellen Sie sicher, dass Sie diese jetzt aufgesetzt haben.

Drücken Sie 'p', um einen Testton abzuspielen. Passen Sie die Systemlautstärke so an, dass Sie den Ton klar und deutlich hören können, er aber nicht unangenehm laut ist.

WICHTIG: Bitte verändern Sie die Lautstärke nach diesem Test während des restlichen Experiments nicht mehr!

Drücken Sie LEERTASTE, wenn die Lautstärke eingestellt ist und Sie fortfahren möchten.
"""
            hp_stim = TextStim(self.win, text=headphone_text, height=0.5, wrapWidth=30)
            hp_stim.draw()
            self.win.flip()
            
            while True:
                hp_keys = event.waitKeys(keyList=["p", "space"])
                if "p" in hp_keys:
                    test_sound.play()
                if "space" in hp_keys:
                    break
            # --------------------------------
            
            # --- Screening Test ---
            loc_text = """
Kopfhörer-Screening: Teil 1 (Ortung)

Wir prüfen nun, ob Ihr System die räumlichen Klänge korrekt wiedergibt.
Sie werden gleich ein einzelnes gesprochenes Zahlwort hören. Ihre Aufgabe ist es anzugeben, aus welcher Richtung das Wort kam.

Wenn Sie einen Kopfhörer falsch herum aufhaben, werden Sie Fehler machen. Bitte prüfen Sie den Sitz (L/R) Ihrer Kopfhörer!

Drücken Sie LEERTASTE, um zu beginnen.
"""
            self.display_text(text=loc_text, keys="space", height=0.5)
            
            screening_errors = 0

            loc_trials = [("4_loc1.wav", "left"), ("7_loc3.wav", "right"), ("2_loc2.wav", "down")]
            for file, correct_key in loc_trials:
                snd = Sound(filename=os.path.join("screening_stimuli", file), device=self.settings["soundconfig"]["device"], mul=self.settings["soundconfig"]["mul"])
                snd.play()
                prompt_stim = TextStim(self.win, text="Woher kam der Ton?\n(Linke Pfeiltaste = Links, Pfeil runter = Mitte, Rechte Pfeiltaste = Rechts)\n\nDrücken Sie 'p' um den Ton erneut abzuspielen.", height=0.5, wrapWidth=30)
                prompt_stim.draw()
                self.win.flip()
                while True:
                    keys = event.waitKeys(keyList=["p", "left", "right", "down"])
                    if "p" in keys:
                        snd.play()
                    else:
                        if keys[0] != correct_key:
                            screening_errors += 1
                        break

            id_text = """
Kopfhörer-Screening: Teil 2 (Erkennung)

Nun prüfen wir, ob Sie die Zahlwörter gut verstehen können.
Sie werden wieder einzelne Zahlwörter hören. Ihre Aufgabe ist es nun anzugeben, welche Zahl (1-9) gesprochen wurde.

Drücken Sie LEERTASTE, um zu beginnen.
"""
            self.display_text(text=id_text, keys="space", height=0.5)
            
            id_trials = [("8_loc2.wav", "8"), ("3_loc1.wav", "3"), ("5_loc3.wav", "5")]
            for file, correct_id in id_trials:
                snd = Sound(filename=os.path.join("screening_stimuli", file), device=self.settings["soundconfig"]["device"], mul=self.settings["soundconfig"]["mul"])
                snd.play()
                prompt_stim = TextStim(self.win, text="Welche Zahl haben Sie gehört? (Zifferntasten 1-9)\n\nDrücken Sie 'p' um den Ton erneut abzuspielen.", height=0.5, wrapWidth=30)
                prompt_stim.draw()
                self.win.flip()
                while True:
                    keys = event.waitKeys(keyList=["p", "1", "2", "3", "4", "5", "6", "7", "8", "9", "num_1", "num_2", "num_3", "num_4", "num_5", "num_6", "num_7", "num_8", "num_9"])
                    if "p" in keys:
                        snd.play()
                    else:
                        ans = keys[0].replace("num_", "")
                        if ans != correct_id:
                            screening_errors += 1
                        break

            if screening_errors > 0:
                abort_text = """
Screening nicht bestanden!

Leider haben Sie einen oder mehrere Fehler im Screening gemacht.
Dies deutet darauf hin, dass Sie entweder keine Kopfhörer tragen, diese falsch herum aufhaben (L/R vertauscht), oder die räumlichen Klänge nicht richtig wahrnehmen können.

Das Experiment wird daher nun abgebrochen. Vielen Dank für Ihr Interesse.

Drücken Sie eine beliebige Taste zum Beenden.
"""
                self.display_text(text=abort_text, keys=None, height=0.5)
                
                # Delete logs
                import glob
                log_dir = self.settings.get("filepaths", {}).get("logs", "logs")
                data_dir = self.settings.get("filepaths", {}).get("data", "data")
                created_files = glob.glob(os.path.join(log_dir, f"*{self.output_str}*")) + glob.glob(os.path.join(data_dir, f"*{self.output_str}*"))
                for file_path in created_files:
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
                core.quit()

            self.display_text(text="Screening bestanden!\nVielen Dank. Das eigentliche Experiment beginnt nun mit einer ausführlichen Einführung.\n\nDrücken Sie LEERTASTE, um fortzufahren.", keys="space", height=0.5)
            # --------------------------------
        # ----------------------------

        # welcome the participant
        self.display_text(text=prompts.prompt1, keys="space", height=0.75)
        self.display_text(text=prompts.prompt2, keys="space", height=0.75)
        self.display_text(text=prompts.prompt3, keys="space", height=0.75)
        self.display_text(text=prompts.prompt4, keys="space", height=0.75)
        if self.test:
            if self.settings["mode"]["demo"]:
                self.run_demo()
            if self.settings["mode"]["acc_test"]:
                self.run_accuracy_test()
            if self.settings["session"]["response_device"] == "mouse":
                self.display_text(text=prompts.prompt5, keys="space", height=0.75)
                self.display_text(text=prompts.prompt6, keys="space", height=0.75)
            elif self.settings["session"]["response_device"] == "keypad":
                self.display_text(text=prompts.prompt7, keys="space", height=0.75)
            self.display_text(text=prompts.get_cue_instruction(os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_0.csv")),
                              keys="space", height=0.75)
            self.display_text(text=prompts.testing, keys="space", height=0.75)
            self.set_block(block=1)  # intentionally choose block within
            self.load_sequence()
            self.create_trials(n_trials=15,
                               durations=(self.settings["session"]["cue_duration"],
                                          None,
                                          self.settings["session"]["stimulus_duration"],
                                          self.settings["session"]["response_duration"],
                                          None),
                               timing=self.settings["session"]["timing"])
            self.start_experiment()
            for trial in self.trials:
                trial.run()
        else:
            self.display_text(text=prompts.get_cue_instruction(os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_0.csv")),
                              keys="space", height=0.75)
            for block in self.blocks:
                self.send_trigger("block_onset")
                # do camera calibration if enabled
                if self.settings["mode"]["camera"]:
                    self.camera_calibration()
                self.display_text("Drücken Sie LEERTASTE, um zu beginnen.", keys="space",
                                  height=0.75)
                self.set_block(block=block)
                self.load_sequence()
                self.create_trials(n_trials=self.n_trials,
                                   durations=(self.settings["session"]["cue_duration"],
                                              None,
                                              self.settings["session"]["stimulus_duration"],
                                              self.settings["session"]["response_duration"],
                                              None),
                                   timing=self.settings["session"]["timing"])
                if block == starting_block:
                    self.start_experiment()
                else:
                    self.first_trial = True
                    self.timer.reset()
                    # self.clock.reset()
                for trial in self.trials:
                    trial.run()
                self.send_trigger("block_offset")
                self.save_data()
                if not block == max(self.blocks):
                    from psychopy.visual import TextStim
                    from psychopy import core
                    pause_stim = TextStim(self.win, text=prompts.pause, height=0.75, wrapWidth=30)
                    pause_stim.draw()
                    self.win.flip()
                    core.wait(60)
        self.display_text(text=prompts.end, keys="q", height=0.75)
        self.send_trigger("experiment_offset")

    # Function to send trigger value by specifying event name
    def send_trigger(self, trigger_name):
        print(trigger_name)
        print(EEG_TRIGGER_MAP[trigger_name])
        if self.settings["mode"]["record_eeg"]:
            # get corresponding trigger value:
            trigger_value = EEG_TRIGGER_MAP[trigger_name]
            # send trigger to EEG:
            self.port.setData(trigger_value)
            core.wait(0.002)
            # turn off EEG trigger
            self.port.setData(0)
        else:
            pass

    def run_accuracy_test(self):
        self.display_text(text=prompts.accuracy_instruction, keys="space", height=0.75)
        round_accuracies = []
        while True:
            stimuli_sequence = []
            available_digits = list(range(1, 10))  # Digits 1 to 9
            while len(stimuli_sequence) < 10:
                # add one additional random digit
                if len(stimuli_sequence) == 9:
                    stimuli_sequence.append(random.choice(self.targets))
                    break
                # Choose a random digit
                digit = random.choice(available_digits)
                available_digits.remove(digit)  # Remove the chosen digit
                # Randomly select either target or control
                if random.choice([True, False]):
                    stimuli_sequence.append(self.targets[digit - 1])  # -1 for 0-based indexing
                else:
                    stimuli_sequence.append(self.controls[digit - 1])
            random.shuffle(stimuli_sequence)
            correct_count = 0
            for stimulus in stimuli_sequence:
                stimulus.play(latency="low", blocksize=0, mapping=[np.random.randint(1, 4)])
                #self.display_text(text="L oder M?")
                psychopy.visual.TextStim(win=self.win, text="L", bold=True, color=[-1, 1, -1], pos=[2, 0]).draw()
                psychopy.visual.TextStim(win=self.win, text="M", bold=True, color=[1, -1, -1], pos=[-2, 0]).draw()
                psychopy.visual.TextStim(win=self.win, text="oder", bold=False).draw()
                self.win.flip()
                keys = event.waitKeys(keyList=['l', 'm'])
                if (keys[0] == 'l' and stimulus in self.targets) or (keys[0] == 'm' and stimulus in self.controls):
                    correct_count += 1
                    self.display_text(text="Korrekt!")
                else:
                    self.display_text(text="Falsch!")
                core.wait(0.5)
            accuracy = correct_count / len(stimuli_sequence)
            round_accuracies.append(accuracy)
            self.display_text(text=f"Sie haben {accuracy * 100:.2f}% der Zahlwörter korrekt identifiziert.\n\n"
                                   f"Drücken Sie LEERTASTE, um {'weiterzublättern' if accuracy==1.0 else 'den Test zu wiederholen'}.", keys="space", height=0.75)
            if accuracy == 1.0:
                break
        # Save accuracy and rounds to a CSV file
        with open(os.path.join(self.output_dir, f"accuracy_test_{self.name}.csv"), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Round", "Accuracy"])  # Write header row
            for round_num, accuracy in enumerate(round_accuracies):
                writer.writerow([round_num, accuracy])  # Write data row

    def run_demo(self):
        self.display_text(text=prompts.demo, keys="space", height=0.75)
        for digit in self.targets:
            digit.play(latency="low", blocksize=0, mapping=[np.random.randint(1, 4)])
            core.wait(1.5)

    def camera_calibration(self):
        # participant instructions
        self.display_text(text=prompts.camera_calibration, keys="space",
                          height=0.75)
        self.mouse.setVisible(False)
        # display fixation dot
        self.default_fix.draw()
        # show fixation dot
        self.win.flip()
        # send trigger
        self.send_trigger("camera_calibration_onset")
        core.wait(10)
        self.send_trigger("camera_calibration_offset")


if __name__ == '__main__':
    os.chdir("C:/Users/Max/PycharmProjects/psychopy-experiments/SPACECUE")
    sess = SpaceCueSession(output_str='sub-01', output_dir="logs",
                           settings_file="config.yaml",
                           starting_block=0, test=True)
    sess.set_block(block=1)  # intentionally choose block within
    sess.load_sequence()
    sess.create_trials(n_trials=15,
                       durations=(sess.settings["session"]["cue_duration"],
                                  None,
                                  sess.settings["session"]["stimulus_duration"],
                                  sess.settings["session"]["response_duration"],
                                  None),
                       timing=sess.settings["session"]["timing"])
    sess.win.close()
