from utils.set_logging_level import set_level
from exptools2.core import Trial, Session
import os
os.environ["SD_ENABLE_ASIO"] = "1"
import prompts as prompts
import pandas as pd
from sound import SoundDeviceSound as Sound
from psychopy import parallel, core
from encoding import EEG_TRIGGER_MAP, PRIMING
import numpy as np


class SpaceprimeTrial(Trial):
    def __init__(self, session, trial_nr, phase_durations, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.stim = None
        # HACKY AND NOT RECOMMENDED --> special case to implement ITI jitter
        # add ITI jitter to the trial
        # self.phase_names.append("iti")
        self.phase_durations[-1] = self.session.sequence["ITI-Jitter"].iloc[trial_nr]
        self.trigger_name = None  # this holds the trial-specific trigger name encoding

    def send_trig_and_sound(self):
        self.stim.play(latency="low", blocksize=0)  # not sure whether this does anything ...
        self.wait(delay_ms=80)  # wait for 80 ms because of constant internal delay
        self.session.send_trigger(trigger_name=self.trigger_name)

    def draw(self):
        # do stuff independent of phases
        if self.session.response_device == "mouse":
            self.session.display_response_box()
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


class SpaceprimeSession(Session):
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
        self.digits = []
        if self.settings["mode"]["record_eeg"]:
            self.port = parallel.ParallelPort(0xCFF8)  # set address of port

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
            trial = SpaceprimeTrial(session=self,
                                    trial_nr=trial_nr,
                                    phase_durations=durations,
                                    phase_names=["stim", "response", "iti"],
                                    parameters=dict(self.sequence.iloc[trial_nr],
                                                    block=self.this_block,
                                                    subject_id=self.subject_id),
                                    verbose=True,
                                    timing=timing,
                                    draw_each_frame=True)
            sound_path = os.path.join(trial.session.blockdir, f"s_{trial.trial_nr}.wav")  # s_0, s_1, ... .wav
            trial.stim = Sound(filename=sound_path, device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"])
            trial.trigger_name = f'Target-{int(trial.parameters["TargetLoc"])}-Singleton-{int(trial.parameters["SingletonLoc"])}-{PRIMING[trial.parameters["Priming"]]}'
            self.trials.append(trial)

    def run(self, starting_block):
        self.send_trigger("experiment_onset")
        # welcome the participant
        self.display_text(text=prompts.prompt1, keys="space", wrapWidth=self.win.size[0], height=0.75)
        self.display_text(text=prompts.prompt2, keys="space", wrapWidth=self.win.size[0], height=0.75)
        self.display_text(text=prompts.prompt3, keys="space", wrapWidth=self.win.size[0], height=0.75)
        self.display_text(text=prompts.prompt4, keys="space", wrapWidth=self.win.size[0], height=0.75)
        if self.test:
            if self.settings["mode"]["demo"]:
                self.display_text(text=prompts.demo, keys="space", wrapWidth=self.win.size[0], height=0.75)
                if self.subject_id % 2 == 0:
                    targets = "low"
                elif self.subject_id % 2 != 0:
                    targets = "high"
                self.digits = [Sound(filename=os.path.join(f"stimuli\\targets_{targets}_30_Hz", x),
                                     device=self.settings["soundconfig"]["device"],
                                     mul=self.settings["soundconfig"]["mul"]) for x in os.listdir(f"stimuli\\targets_{targets}_30_Hz")]
                for digit in self.digits:
                    digit.play(latency="low", blocksize=0, mapping=[np.random.randint(1, 4)])
                    core.wait(1.5)
            self.display_text(text=prompts.prompt5, keys="space", wrapWidth=self.win.size[0], height=0.75)
            self.display_text(text=prompts.prompt6, keys="space", wrapWidth=self.win.size[0], height=0.75)
            self.display_text(text=prompts.testing, keys="space", wrapWidth=self.win.size[0], height=0.75)
            self.set_block(block=1)  # intentionally choose block within
            self.load_sequence()
            self.create_trials(n_trials=15,
                               durations=(self.settings["session"]["stimulus_duration"],
                                          self.settings["session"]["response_duration"],
                                          None),
                               timing=self.settings["session"]["timing"])
            self.start_experiment()
            for trial in self.trials:
                trial.run()
        else:
            # do camera calibration if enabled
            if self.settings["mode"]["camera"]:
                # participant instructions
                self.display_text(text=prompts.camera_calibration, keys="space", wrapWidth=self.win.size[0],
                                  height=0.75)
                # display fixation dot
                self.default_fix.draw()
                # show fixation dot
                self.win.flip()
                # send trigger
                self.send_trigger("camera_calibration_onset")
                core.wait(10)
                self.send_trigger("camera_calibration_offset")
            self.display_text("Drücke LEERTASTE, um zu beginnen.", keys="space", wrapWidth=self.win.size[0],
                              height=0.75)
            for block in self.blocks:
                self.send_trigger("block_onset")
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
                    trial.run()
                self.send_trigger("block_offset")
                self.save_data()
                if not block == max(self.blocks):
                    self.display_text(text=prompts.pause, duration=60, wrapWidth=self.win.size[0], height=0.75)
                    self.display_text(text=prompts.pause_finished, keys="space", wrapWidth=self.win.size[0], height=0.75)
        self.display_text(text=prompts.end, keys="q", wrapWidth=self.win.size[0], height=0.75)
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


if __name__ == '__main__':
    # DEBUGGING
    sess = SpaceprimeSession(output_str=f'sub-102', output_dir="logs",
                             settings_file="SPACEPRIME\config.yaml",
                             starting_block=0, test=False)
    sess.send_trigger("experiment_onset")
    # welcome the participant
    sess.display_text(text=prompts.welcome1, keys="space")
    sess.display_text(text=prompts.welcome2, keys="space")
    if sess.settings["mode"]["camera"]:
        sess.display_text(text=prompts.camera_calibration, keys="space")
        sess.default_fix.draw()
        sess.win.flip()
        sess.send_trigger("camera_calibration_onset")
        core.wait(1)
        sess.send_trigger("camera_calibration_offset")
        sess.display_text("Drücke LEERTASTE, um zu beginnen.", keys="space")
    for block in sess.blocks:
        sess.send_trigger("block_onset")
        sess.set_block(block=block)
        sess.load_sequence()
        sess.create_trials(n_trials=5,
                           durations=(sess.settings["session"]["stimulus_duration"],
                                      sess.settings["session"]["response_duration"],
                                      None),  # this is hacky and usually not recommended (for ITI Jitter)
                           timing=sess.settings["session"]["timing"])
        if block == 0:
            sess.start_experiment()
        else:
            sess.timer.reset()
        for trial in sess.trials:
            # make sure the default is black line color
            # self.send_trigger("trial_onset")
            trial.trigger_name = f'Target-{int(trial.parameters["TargetLoc"])}-Singleton-{int(trial.parameters["SingletonLoc"])}-{PRIMING[trial.parameters["Priming"]]}'
            trial.run()
            # self.send_trigger("trial_offset")
        sess.send_trigger("block_offset")
        sess.save_data()
        if not block == max(sess.blocks):
            sess.display_text(text=prompts.pause, keys="space")
    sess.display_text(text=prompts.end, keys="q")
    sess.send_trigger("experiment_offset")
    sess.close()
