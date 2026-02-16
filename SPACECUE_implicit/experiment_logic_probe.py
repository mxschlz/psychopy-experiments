import psychopy.visual

from utils.set_logging_level import set_level
from exptools2.core import Trial, Session
import os
os.environ["SD_ENABLE_ASIO"] = "1"
import prompts as prompts
import pandas as pd
from utils.sound import SoundDeviceSound as Sound
from psychopy import parallel, core, event
from encoding import EEG_TRIGGER_MAP, PRIMING
import random
import numpy as np
import string
import csv
import slab
from utils.signal_processing import spatialize
from encoding import SPACE_ENCODER


class SpacecueImplicitTrial(Trial):
    def __init__(self, session, trial_nr, phase_durations, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.stim = None
        # HACKY AND NOT RECOMMENDED --> special case to implement ITI jitter
        # add ITI jitter to the trial
        # self.phase_names.append("iti")
        self.phase_durations[-1] = self.session.sequence["ITI-Jitter"].iloc[trial_nr]
        self.trigger_name = None  # this holds the trial-specific trigger name encoding
        self.probe_sequence = None  # Placeholder for probe task sequence

    def run(self):
        print(f"TRIAL {self.trial_nr}: Running with task_type = {self.parameters.get('task_type')}") # Uncomment for debugging
        if self.parameters.get("task_type") == "probe":
            self.run_probe()
        else:
            super().run()

    def send_trig_and_sound(self):
        # print(f"Target Digit {self.session.sequence.iloc[self.trial_nr]['TargetDigit']} over Speaker {self.session.sequence.iloc[self.trial_nr]['TargetLoc']}")
        # print(f"Distractor Digit {self.session.sequence.iloc[self.trial_nr]['SingletonDigit']} over Speaker {self.session.sequence.iloc[self.trial_nr]['SingletonLoc']}")
        self.stim.play(latency="low", blocksize=0)  # not sure whether this does anything ...
        self.wait(delay_ms=80)  # wait for 80 ms because of constant internal delay
        self.session.send_trigger(trigger_name=self.trigger_name)

    def draw(self):
        # do stuff independent of phases
        if self.session.response_device == "mouse":
            self.session.display_response_box()
            self.track_mouse_pos()
        elif self.session.response_device == "keypad":
            self.session.default_fix.draw()
        # play stimulus in phase 0
        if self.phase == 0:
            if self.session.response_device == "mouse":
                self.session.virtual_response_box[0].lineColor = "black"
                self.session.mouse.setVisible(True)
                self.session.mouse.setPos((0, 0))
            if not self.stim.is_playing():
                self.send_trig_and_sound()
        # get response in phase 1
        if self.phase == 1:
            if any(self.session.mouse.getPressed()):
                pass
                #self.session.mouse.setVisible(False)
        # print too slow warning if response is collected in phase 2
        if self.phase == 2:
            self.stim.stop()  #  reset the sound
            if any(self.get_events()) or any(self.session.mouse.getPressed()):
                if self.session.virtual_response_box:
                    self.session.virtual_response_box[0].lineColor = "red"
                    self.session.mouse.setVisible(False)

    def run_probe(self):
        """Executes the probe task: Play letters, get recall."""
        # Manually set start_trial to enable RT calculation without logging a separate event row
        self.start_trial = self.session.clock.getTime()
        # --- Search Stimulus Presentation ---
        self.session.mouse.setVisible(True)
        if self.session.response_device == "mouse":
            self.session.display_response_box()
        self.session.win.flip()

        # Play search stimulus
        self.stim.play(latency="low", blocksize=0)
        core.wait(self.session.settings["session"]["stimulus_duration"])
        #core.wait(0.1)  # Gap between search stimulus and probe task

        # --- Phase 0: Stimulation (Play 9 letters) ---
        #self.log_phase_info(phase=3)

        # Hide mouse during listening
        # self.session.mouse.setVisible(False)
        self.session.input_text.text = ""
        for key in self.session.visual_keyboard:
            key.draw()
        self.session.input_text.draw()
        self.session.win.flip()

        # Play the sequence generated in create_trials
        # Sequence structure: [{'sound': mixed_sound_obj, 'chars': [...]}, ...]
        for step in self.probe_sequence:
            print(f"Playing probe step: {step.get('chars')}")
            step['sound'].play(latency="low", blocksize=0)

            # Wait for sound to finish + gap (approx 500ms sound + 200ms gap)
            # Using core.wait is acceptable here as we aren't animating visuals
            #core.wait(0.4)

        # --- Phase 1: Response (Visual Keyboard) ---
        #self.log_phase_info(phase=1)

        response_string = ""
        self.session.input_text.text = response_string
        #self.session.mouse.setVisible(True)
        #self.session.mouse.setPos((0, 0))
        self.session.mouse.clickReset()

        # Custom loop for response collection
        while True:
            # Draw keyboard
            for key in self.session.visual_keyboard:
                key.draw()
            self.session.input_text.draw()
            self.session.win.flip()

            # Consume keyboard events to prevent them from leaking to the next trial
            keys = event.getKeys()
            for key, t in keys:
                print(f"DEBUG: Key pressed in probe loop: {key}")
                if key == 'q':
                    self.session.close()
                    self.session.quit()
                    return

            # Check for clicks
            if self.session.mouse.getPressed()[0]:
                if not self.session.mouse_was_pressed:
                    for key in self.session.visual_keyboard:
                        if key.contains(self.session.mouse):
                            if key.text == "FERTIG":
                                # Log the full response and exit
                                print(f"DEBUG: Finishing probe trial with response: {response_string}")
                                self.phase = 3
                                self._log_event("probe_response", response_string, self.session.clock.getTime())
                                self.session.timer.reset()
                                event.clearEvents()
                                return
                            elif key.text == "DEL":
                                response_string = response_string[:-1]
                            else:
                                response_string += key.text
                            self.session.input_text.text = response_string
                    self.session.mouse_was_pressed = True
            else:
                self.session.mouse_was_pressed = False


class SpacecueImplicitSession(Session):
    def __init__(self, output_str, output_dir=None, settings_file=None, starting_block=0, test=False):
        if not isinstance(output_str, str):
            print(f"output_str must be of type str, got {type(output_str)}")
            output_str = str(output_str)
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file)
        self.blocks = range(starting_block, self.settings["session"]["n_blocks"])
        self.n_trials = self.settings["session"]["n_trials"]
        self.blockdir = str
        self.sequence = pd.DataFrame
        self.logger = set_level(self.settings["logging"]["level"])
        self.test = test
        self.this_block = None
        self.subject_id = int(self.output_str.split("-")[1])
        self.subj_id_is_even = True if self.subject_id % 2 == 0 else False
        self.targets = [Sound(filename=os.path.join("stimuli\\targets_low_30_Hz", x),
                              device=self.settings["soundconfig"]["device"],
                              mul=self.settings["soundconfig"]["mul"]) for x in
                        os.listdir(f"stimuli\\targets_low_30_Hz")]
        self.controls = [Sound(filename=os.path.join("stimuli\\digits_all_250ms", x),
                               device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"]) for x in
                         os.listdir(f"stimuli\\digits_all_250ms")]

        # Load letters for probe task
        # Assuming stimuli/letters exists and contains wav files like "A.wav", "B.wav"
        self.letters = []
        self.letter_sounds = {} # Map char -> sound object (or dict of spatialized sounds)
        # --- MODIFICATION: Only load probe stimuli if probability > 0 ---
        if self.settings["session"].get("probe_task_prob", 0.0) > 0:
            letters_path = os.path.join(self.settings["filepaths"]["stimuli"], "letters")
            if os.path.isdir(letters_path):
                for f in os.listdir(letters_path):
                    if f.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
                        char = os.path.splitext(f)[0].upper()
                        self.letters.append(char)
                        full_path = os.path.join(letters_path, f)

                        if self.settings["mode"]["freefield"]:
                            s = Sound(filename=full_path,
                                      device=self.settings["soundconfig"]["device"],
                                      mul=self.settings["soundconfig"]["mul"])
                            self.letter_sounds[char] = s
                        else:
                            # Headphone mode: Load and spatialize for all 3 locations
                            s_slab = slab.Sound.read(full_path)
                            s_slab.level = self.settings["session"]["level"]
                            s_bin = slab.Binaural(s_slab)

                            self.letter_sounds[char] = {}
                            for loc in [1, 2, 3]:
                                azi, ele = SPACE_ENCODER[loc]
                                spatialized = spatialize(s_bin, azi=azi, ele=ele)
                                self.letter_sounds[char][loc] = Sound(data=spatialized.data,
                                                                      sr=spatialized.samplerate,
                                                                      device=self.settings["soundconfig"]["device"],
                                                                      mul=self.settings["soundconfig"]["mul"])

        self.create_visual_keyboard()

        if self.settings["mode"]["record_eeg"]:
            self.port = parallel.ParallelPort(0xCFF8)  # set address of port
        self.randomize_locations = self.settings["numpad"].get("randomize_locations", False)

    def create_visual_keyboard(self):
        """Creates a visual keyboard for the probe task."""
        self.visual_keyboard = []
        keys = list(string.ascii_uppercase)
        # Create a grid of letters
        start_x, start_y = -6, 4
        x, y = start_x, start_y
        for k in keys:
            self.visual_keyboard.append(psychopy.visual.TextStim(self.win, text=k, pos=(x, y), height=1.5))
            x += 2.5
            if x > 6:
                x = start_x
                y -= 2.5

        # Add special keys
        self.visual_keyboard.append(psychopy.visual.TextStim(self.win, text="DEL", pos=(-3, y-2), height=1, color='red'))
        self.visual_keyboard.append(psychopy.visual.TextStim(self.win, text="FERTIG", pos=(3, y-2), height=1, color='green'))

        # Text stimulus to show what user typed
        self.input_text = psychopy.visual.TextStim(self.win, text="", pos=(0, 6), height=1.5, color='yellow')

    def display_response_box(self):
        for stimulus in self.virtual_response_box:
            stimulus.draw()

    def configure_response_box(self, active_digits):
        """Configures the response box to show only active digits."""
        display_presented_only = self.settings["numpad"].get("display_presented_sounds_only", True)

        if self.virtual_response_box:
            active_stimuli = []
            # Skip the first element (guide)
            for stim in self.virtual_response_box[1:]:
                if not display_presented_only or stim.text in active_digits:
                    active_stimuli.append(stim)
                else:
                    stim.pos = (10000, 10000)  # Move off-screen

            # Recalculate positions for active stimuli
            if active_stimuli and self.settings["numpad"].get("layout") == "circle":
                size = self.settings["numpad"]["size"]
                radius = size / 2

                equilateral = self.settings["numpad"].get("rotate_triangle", False)

                if equilateral and len(active_stimuli) == 3:
                    # Equilateral triangle (0, 120, 240) + random rotation
                    angles = np.linspace(0, 360, 3, endpoint=False) + np.random.uniform(0, 360)
                else:
                    angles = np.linspace(180, 0, len(active_stimuli))

                if self.randomize_locations:
                    np.random.shuffle(angles)

                for i, stim in enumerate(active_stimuli):
                    angle_rad = np.deg2rad(angles[i])
                    x_pos = radius * np.cos(angle_rad)
                    y_pos = radius * np.sin(angle_rad)
                    stim.pos = (x_pos, y_pos)

    def set_block(self, block):
        self.blockdir = os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_{block}")
        self.display_text(text=f"Initialisiere Block {block+1} von insgesamt {max(self.blocks)+1}... ",
                          duration=3.0)
        self.this_block = block

    def load_sequence(self):
        print("Loading sequence")
        self.sequence = pd.read_csv(self.blockdir + ".csv")

    def create_trials(self, n_trials, durations, timing="seconds"):
        print("Creating trials")

        # Determine which trials are probe
        prob = self.settings["session"].get("probe_task_prob", 0.0)

        # --- MODIFICATION: Skip logic if prob is 0 ---
        if prob > 0:
            n_probe = int(n_trials * prob)
            n_search = n_trials - n_probe
            print(f"Generating sequence: {n_search} search, {n_probe} probe trials ({prob:.1%}).")

            # Generate task types ensuring no consecutive probe trials
            if n_probe > n_search:
                print("Warning: Too many probe trials to guarantee separation. Using random shuffle.")
                task_types = ["search"] * n_search + ["probe"] * n_probe
                random.shuffle(task_types)
                # Ensure first trial is search
                if task_types[0] == "probe":
                    for i in range(1, len(task_types)):
                        if task_types[i] == "search":
                            task_types[0], task_types[i] = task_types[i], task_types[0]
                            break
            else:
                # Construct sequence with guaranteed separation
                # We have n_search slots around the search trials (1 to n_search) to avoid start.
                # We randomly select n_probe slots to fill with a probe trial.
                probe_slots = set(random.sample(range(1, n_search + 1), n_probe))

                task_types = []
                for i in range(n_search):
                    if i in probe_slots:
                        task_types.append("probe")
                    task_types.append("search")
                # Check the last slot (after the last search trial)
                if n_search in probe_slots:
                    task_types.append("probe")

            # Verify sequence
            seq_str = "".join(["P" if t == "probe" else "S" for t in task_types])
            print(f"Probe trial indices: {[i for i, t in enumerate(task_types) if t == 'probe']}")
            for i in range(len(task_types) - 1):
                if task_types[i] == "probe" and task_types[i + 1] == "probe":
                    print(f"WARNING: Consecutive probes detected at index {i}!")
        else:
            print("Probe probability is 0. All trials are search trials.")
            task_types = ["search"] * n_trials
        # ---------------------------------------------

        self.trials = []
        for trial_nr in range(n_trials):
            # Add task_type to parameters so it gets logged
            params = dict(self.sequence.iloc[trial_nr],
                          block=self.this_block,
                          subject_id=self.subject_id,
                          task_type=task_types[trial_nr])

            trial = SpacecueImplicitTrial(session=self,
                                          trial_nr=trial_nr,
                                          phase_durations=durations,
                                          phase_names=["stim", "response", "iti"],
                                          parameters=params,
                                          verbose=True,
                                          timing=timing,
                                          draw_each_frame=True)
            sound_path = os.path.join(trial.session.blockdir, f"s_{trial.trial_nr}.wav")  # s_0, s_1, ... .wav
            trial.stim = Sound(filename=sound_path, device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"])
            trial.trigger_name = f'Target-{int(trial.parameters["TargetLoc"])}-Singleton-{int(trial.parameters["SingletonLoc"])}-{PRIMING[trial.parameters["Priming"]]}'

            # If probe task, generate the sequence of letters
            if task_types[trial_nr] == "probe":
                seq = []
                locations = [1, 2, 3]
                # Generate streams for each location
                streams = {}

                n_steps = self.settings["session"].get("n_probe_time_steps", 1)
                n_total_letters = 3 * n_steps

                # Sample unique letters to ensure no duplicates in the trial
                if len(self.letters) >= n_total_letters:
                    trial_letters = random.sample(self.letters, n_total_letters)
                    for i, loc in enumerate(locations):
                        streams[loc] = trial_letters[i * n_steps:(i + 1) * n_steps]
                else:
                    for loc in locations:
                        if len(self.letters) >= n_steps:
                            streams[loc] = random.sample(self.letters, n_steps)
                        else:
                            streams[loc] = [random.choice(self.letters) for _ in range(n_steps)] if self.letters else []

                # Add probe info to trial parameters for logging
                for loc in locations:
                    if loc in streams:
                        for step_idx, char in enumerate(streams[loc]):
                            trial.parameters[f"Probe_Loc{loc}_Step{step_idx + 1}"] = char

                # Create time steps (mixing sounds for simultaneous playback)
                for step_idx in range(n_steps):
                    sounds_to_mix = []
                    max_samples = 0

                    # Gather data for this step
                    for loc in locations:
                        if not streams[loc]: continue
                        char = streams[loc][step_idx]

                        if self.settings["mode"]["freefield"]:
                            s_obj = self.letter_sounds[char]
                            data = s_obj.data
                            # Ensure 2D (samples, channels)
                            if data.ndim == 1:
                                data = data[:, np.newaxis]
                        else:
                            s_obj = self.letter_sounds[char][loc]
                            data = s_obj.data

                        if data.shape[0] > max_samples:
                            max_samples = data.shape[0]
                        sounds_to_mix.append((loc, data))

                    # Create mixture array
                    n_channels = 3 if self.settings["mode"]["freefield"] else 2
                    mixture = np.zeros((max_samples, n_channels), dtype=np.float32)

                    # Mix sounds
                    for loc, data in sounds_to_mix:
                        padded = np.zeros((max_samples, data.shape[1]), dtype=np.float32)
                        padded[:data.shape[0], :] = data

                        if self.settings["mode"]["freefield"]:
                            # Map loc 1->ch0, 2->ch1, 3->ch2 (assuming mono source or taking 1st channel)
                            mixture[:, loc - 1] += padded[:, 0]
                        else:
                            # Headphones: add stereo signal
                            mixture += padded

                    # Create mixed Sound object
                    mixed_sound = Sound(data=mixture,
                                        sr=self.settings["session"]["samplerate"],
                                        device=self.settings["soundconfig"]["device"],
                                        mul=self.settings["soundconfig"]["mul"])

                    seq.append({
                        'sound': mixed_sound,
                        'chars': [streams[loc][step_idx] for loc in locations if streams[loc]]
                    })

                trial.probe_sequence = seq

            self.trials.append(trial)

    def run(self, starting_block):
        print("Running experiment")
        # self.send_trigger("experiment_onset")
        # welcome the participant
        self.display_text(text=prompts.prompt1, keys="space", height=0.75)
        self.display_text(text=prompts.prompt2, keys="space", height=0.75)
        self.display_text(text=prompts.prompt3, keys="space", height=0.75)
        self.display_text(text=prompts.prompt4, keys="space", height=0.75)
        if self.test:
            print("Running test")
            if self.settings["mode"]["demo"]:
                print("Running demo")
                self.run_demo()
            if self.settings["mode"]["acc_test"]:
                print("Running accuracy test")
                self.run_accuracy_test()
            self.display_text(text=prompts.prompt5, keys="space", height=0.75)
            self.display_text(text=prompts.prompt6, keys="space", height=0.75)
            self.display_text(text=prompts.testing, keys="space", height=0.75)
            self.set_block(block=1)  # intentionally choose block within
            self.load_sequence()
            self.create_trials(n_trials=15,
                               durations=(self.settings["session"]["stimulus_duration"],
                                          self.settings["session"]["response_duration"],
                                          None),
                               timing=self.settings["session"]["timing"])
            self.start_experiment()
            for trial in self.trials:
                # Extract active digits
                active_digits = []
                for key in ["TargetDigit", "SingletonDigit", "Non-Singleton1Digit", "Non-Singleton2Digit"]:
                    if key in trial.parameters and pd.notna(trial.parameters[key]):
                        active_digits.append(str(int(trial.parameters[key])))
                self.configure_response_box(active_digits)
                #print(trial.parameters)
                trial.run()
        else:
            for block in self.blocks:
                print(f"Running block {block}")
                self.send_trigger("block_onset")
                # do camera calibration if enabled
                if self.settings["mode"]["camera"]:
                    self.camera_calibration()
                self.display_text("Drücken Sie LEERTASTE, um zu beginnen.", keys="space",
                                  height=0.75)
                self.set_block(block=block)
                self.load_sequence()
                self.create_trials(n_trials=self.n_trials,
                                   durations=(self.settings["session"]["stimulus_duration"],
                                              self.settings["session"]["response_duration"],
                                              None),  # this is hacky and usually not recommended (for ITI Jitter)
                                   timing=self.settings["session"]["timing"])
                if block == starting_block:
                    self.start_experiment()
                else:
                    self.first_trial = True
                    self.timer.reset()
                    # self.clock.reset()
                for trial in self.trials:
                    # Extract active digits
                    active_digits = []
                    for key in ["TargetDigit", "SingletonDigit", "Non-Singleton1Digit", "Non-Singleton2Digit"]:
                        if key in trial.parameters and pd.notna(trial.parameters[key]):
                            active_digits.append(str(int(trial.parameters[key])))
                    self.configure_response_box(active_digits)
                    trial.run()
                self.send_trigger("block_offset")
                print(f"Stopping block {block}")
                self.save_data()

                accuracies = []
                for t in self.trials:
                    if t.last_resp is not None:
                        accuracies.append(str(t.parameters['TargetDigit']) == str(t.last_resp))

                if accuracies:
                    mean_acc = np.mean(accuracies)
                    print(f"Block accuracy: {mean_acc}")
                    self.display_text(text=f"Genauigkeit im letzten Block: {mean_acc:.1%}", duration=3.0, height=0.75)

                if not block == max(self.blocks):
                    #self.display_text(text=prompts.pause, duration=60, height=0.75)
                    self.display_text(text=prompts.pause_finished, keys="space", height=0.75)
        self.display_text(text=prompts.end, keys="q", height=0.75)
        # self.send_trigger("experiment_offset")

    # Function to send trigger value by specifying event name
    def send_trigger(self, trigger_name):
        #print(trigger_name)
        #print(EEG_TRIGGER_MAP[trigger_name])
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

    def bbtkv2_test_run(self, n_trials):
        # set block
        self.set_block(block=1)
        # load up trial sequence
        self.load_sequence()
        # create trials from sequence
        self.create_trials(n_trials=n_trials,
                           durations=(self.settings["session"]["stimulus_duration"],
                                      self.settings["session"]["response_duration"],
                                      None),  # this is hacky and usually not recommended (for ITI Jitter)
                           timing=self.settings["session"]["timing"])
        # set up timer etc. for the experiment
        self.start_experiment()
        # run through trials
        for trial in self.trials:
            trial.trigger_name = "test_trigger"
            # play sound
            trial.run()
        # clean up
        self.close()
        self.quit()

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
                l = psychopy.visual.TextStim(win=self.win, text="L", bold=True, color=[-1, 1, -1], pos=[2, 0]).draw()
                m = psychopy.visual.TextStim(win=self.win, text="M", bold=True, color=[1, -1, -1], pos=[-2, 0]).draw()
                oder = psychopy.visual.TextStim(win=self.win, text="oder", bold=False).draw()
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
            loc = np.random.randint(1, 4)
            if self.settings["mode"]["freefield"]:
                digit.play(latency="low", blocksize=0, mapping=[loc])
            else:
                # Headphone mode: Spatialize
                s_slab = slab.Sound(data=digit.data, samplerate=digit.sr)
                s_bin = slab.Binaural(s_slab)
                azi, ele = SPACE_ENCODER[loc]
                spatialized_s = spatialize(s_bin, azi=azi, ele=ele)
                s_out = Sound(data=spatialized_s.data, sr=spatialized_s.samplerate,
                              device=self.settings["soundconfig"]["device"], mul=0)
                s_out.play()
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
    pass