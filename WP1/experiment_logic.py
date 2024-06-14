from exptools2.core import Trial, Session
from exptools2 import utils
import slab
from datetime import datetime
import os
import WP1.prompts as prompts
import pandas as pd

from psychopy.sound import Sound


class WP1Trial(Trial):
    def __init__(self, session, trial_nr, phase_durations, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.stim = slab.Binaural

    def draw(self):
        # play stimulus in phase 0
        if self.phase == 0:
            self.stim.play()
            #self.stim.pause()
        # get response in phase 1
        if self.phase == 1:
            pass
        # do nothing in phase 2
        if self.phase == 2:
            pass


class WP1Session(Session):
    def __init__(self, output_str, output_dir=None, settings_file=None):
        """ Initializes TestSession object. """
        if not isinstance(output_str, str):
            print(f"output_str must be of type str, got {type(output_str)}")
            output_str = str(output_str)
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file)
        self.blocks = range(self.settings["session"]["n_blocks"])
        self.n_trials = self.settings["session"]["n_trials"]
        self.start_time = datetime.now()  # starting date time
        self.name = f"{output_str}_{self.start_time.strftime('%B_%d_%Y_%H_%M_%S')}"
        self.blockdir = str
        self.sequence = pd.DataFrame

    def set_block(self, block):
        self.blockdir = os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_{block}")

    def load_sequence(self):
        self.sequence = pd.read_excel(self.blockdir + ".xlsx")

    def create_trials(self, durations=(.5, .5), timing='seconds'):
        self.trials = []
        for trial_nr in range(self.n_trials):
            trial = WP1Trial(session=self,
                             trial_nr=trial_nr,
                             phase_durations=durations,
                             phase_names=["stim", "response", "iti"],
                             parameters=dict(self.sequence.iloc[trial_nr]),
                             verbose=True,
                             timing=timing)
            sound_path = os.path.join(trial.session.blockdir, f"s_{trial_nr}.wav")  # s_0, s_1, ... .wav
            trial.stim = slab.Binaural.read(sound_path)
            self.trials.append(trial)

    def run(self):
        # welcome the participant
        self.display_text(text=prompts.welcome, keys="space")
        for block in self.blocks:
            self.default_fix.draw()
            self.set_block(block=block)
            self.create_trials(durations=(self.settings["session"]["stimulus_duration"],
                                          self.settings["session"]["response_duration"],
                                          self.settings["session"]["iti"]),
                               timing=self.settings["session"]["timing"])
            self.start_experiment()
            for trial in self.trials:
                trial.run()
            self.display_text(text=prompts.pause, keys="space")
        self.display_text(text=prompts.end, keys="space")
        # utils.save_experiment(self, output_str=self.name)


if __name__ == '__main__':
    import time
    # DEBUGGING
    sess = WP1Session(output_str='sub-99', output_dir="logs", settings_file="WP1/config.yaml")
    sess.set_block(block=0)
    sess.load_sequence()
    sess.start_experiment()
    sess.run()
    sess.quit()
