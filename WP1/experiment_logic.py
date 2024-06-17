from exptools2.core import Trial, Session
import os
import WP1.prompts as prompts
import pandas as pd
from utils import set_logging_level
import numpy as np
import time

from psychopy.sound import Sound


class WP1Trial(Trial):
    def __init__(self, session, trial_nr, phase_durations, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.stim = Sound

    def draw(self):
        self.session.default_fix.draw()
        # play stimulus in phase 0
        if self.phase == 0:
            self.stim.play()
            time.sleep(self.stim.duration)

        # get response in phase 1
        if self.phase == 1:
            while self.session.timer.getTime() < 0:
                if self.current_key is not None:
                    if self.current_key != self.session.sequence.iloc[self.trial_nr]["TargetDigit"]:
                        self.session.display_text(text=prompts.error_notification, color=(1.0, 0.0, 0.0),
                                                  duration=np.abs(self.session.timer.getTime()))

        # print too slow warning if response is collected in phase 2
        if self.phase == 2:
            if self.session.test:
                while self.session.timer.getTime() < 0:
                    if any(self.get_events()):
                        self.session.display_text(text=prompts.too_slow, color=(1.0, 0.0, 0.0),
                                                  duration=np.abs(self.session.timer.getTime()))  # red warning


class WP1Session(Session):
    def __init__(self, output_str, output_dir=None, settings_file=None, starting_block=0, test=False):
        if not isinstance(output_str, str):
            print(f"output_str must be of type str, got {type(output_str)}")
            output_str = str(output_str)
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file)
        self.blocks = range(starting_block, self.settings["session"]["n_blocks"])
        self.n_trials = self.settings["session"]["n_trials"]
        self.blockdir = str
        self.sequence = pd.DataFrame
        self.logger = set_logging_level.set_level(self.settings["logging"]["level"])
        self.test = test
        # slab.set_default_level(self.settings["session"]["level"])
        # print(f"Set stimulus level to {slab.sound._default_level}")

    def set_block(self, block):
        self.blockdir = os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_{block}")
        self.display_text(text=f"Initializing block {block} ... ", duration=3.0)

    def load_sequence(self):
        self.sequence = pd.read_excel(self.blockdir + ".xlsx")

    def create_trials(self, n_trials, durations=(.5, .5), timing='seconds'):
        self.trials = []
        for trial_nr in range(n_trials):
            trial = WP1Trial(session=self,
                             trial_nr=trial_nr,
                             phase_durations=durations,
                             phase_names=["stim", "response", "iti"],
                             parameters=dict(self.sequence.iloc[trial_nr]),
                             verbose=True,
                             timing=timing)
            sound_path = os.path.join(trial.session.blockdir, f"s_{trial_nr}.wav")  # s_0, s_1, ... .wav
            trial.stim = Sound(sound_path)
            # trial.stim = slab.Binaural.read(sound_path)
            self.trials.append(trial)

    def run(self):
        # welcome the participant
        self.display_text(text=prompts.welcome, keys="space")
        if self.test:
            self.display_text(text=prompts.testing, keys="space")
            self.set_block(block=0)
            self.load_sequence()
            self.create_trials(n_trials=10,  # TODO: more testing trials?
                               durations=(self.settings["session"]["stimulus_duration"],
                                          self.settings["session"]["response_duration"],
                                          self.settings["session"]["iti"]),
                               timing=self.settings["session"]["timing"])
            self.start_experiment()
            for trial in self.trials:
                trial.run()
        else:
            for block in self.blocks:
                self.set_block(block=block)
                self.load_sequence()
                self.create_trials(n_trials=self.n_trials,
                                   durations=(self.settings["session"]["stimulus_duration"],
                                              self.settings["session"]["response_duration"],
                                              self.settings["session"]["iti"]),
                                   timing=self.settings["session"]["timing"])
                self.start_experiment()
                for trial in self.trials:
                    trial.run()
                self.display_text(text=prompts.pause, keys="space")
        self.display_text(text=prompts.end, keys="space")


if __name__ == '__main__':
    # DEBUGGING
    sess = WP1Session(output_str='sub-99', output_dir="WP1/logs", settings_file="WP1/config.yaml")
    # utils.save_experiment(sess, output_str=sess.name)
    sess.set_block(block=0)
    sess.load_sequence()
    sess.create_trials(n_trials=sess.n_trials,
                       durations=(sess.settings["session"]["stimulus_duration"],
                                  sess.settings["session"]["response_duration"],
                                  sess.settings["session"]["iti"]),
                       timing=sess.settings["session"]["timing"])
    sess.win.close()

    # sess.run()
    # sess.quit()
