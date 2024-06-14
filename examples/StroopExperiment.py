import random
from exptools2.core import Trial, Session
from psychopy import visual
from utils import set_logging_level


class StroopTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations, phase_names,
                 parameters, timing, load_next_during_phase,
                 verbose, condition='congruent'):
        """ Initializes a StroopTrial object. """
        super().__init__(session, trial_nr, phase_durations, phase_names,
                         parameters, timing, load_next_during_phase, verbose)
        self.condition = condition
        self.fixation_dot = visual.Circle(self.session.win, radius=0.1, edges=100)

        if self.condition == 'congruent':
            self.word = visual.TextStim(self.session.win, text='red', color=(1, 0, 0))  # red!
        else:
            self.word = visual.TextStim(self.session.win, text='red', color=(0, 1, 0))  # green!

    def draw(self):
        if self.phase == 0:  # Python starts counting from 0, and so should you
            self.word.draw()
        else:  # assuming that there are only 2 phases
            self.fixation_dot.draw()


class StroopSession(Session):

    def __init__(self, output_str, output_dir, settings_file, n_trials):
        super().__init__(output_str, output_dir, settings_file)  # initialize parent class!
        self.n_trials = n_trials  # just an example argument
        self.trials = []  # will be filled with Trials later
        self.logger = set_logging_level.set_level(self.settings["logger"]["level"])

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """
        conditions = ['congruent' if i % 2 == 0 else 'incongruent'
                      for i in range(self.n_trials)]
        random.shuffle(conditions)

        for i in range(self.n_trials):
            trial = StroopTrial(
                session=self,
                trial_nr=i,
                phase_durations=(2, 1),
                timing='seconds',
                phase_names=('word', 'fix'),
                parameters={'condition': conditions[i]},
                load_next_during_phase=None,
                verbose=True,
                condition=conditions[i]
            )
            self.trials.append(trial)

    def run(self):
        self.create_trials()
        self.start_experiment()

        for trial in self.trials:
            trial.run()

        self.close()


if __name__ == '__main__':

    my_sess = StroopSession(output_str='sub-01', output_dir='../WP1/logs', settings_file='../WP1/config.yaml', n_trials=10)
    my_sess.run()
