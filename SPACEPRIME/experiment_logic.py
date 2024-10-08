from exptools2.core import Trial, Session
import os
import prompts as prompts
import pandas as pd
from SPACEPRIME.utils import set_logging_level
#from psychopy.sound import Sound
from sound import Sound
from psychopy import parallel, core
from encoding import EEG_TRIGGER_MAP, PRIMING
import psychopy


class SpaceprimeTrial(Trial):
    def __init__(self, session, trial_nr, phase_durations, **kwargs):
        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.stim = Sound
        # HACKY AND NOT RECOMMENDED --> special case to implement ITI jitter
        # add ITI jitter to the trial
        # self.phase_names.append("iti")
        self.phase_durations[-1] = self.session.sequence["ITI-Jitter"].iloc[trial_nr]
        self.trigger_name = None

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
            # if not self.stim.isPlaying:  # wait until stimulus is presented TODO: use this with psychopy Sound class
            self.session.send_trigger(self.trigger_name)
            self.stim.play()
            core.wait(self.stim.duration)
            # core.wait(self.stim.duration)

        # get response in phase 1
        if self.phase == 1:
            # while self.session.timer.getTime() < 0:
            # if self.current_key is not None:
            # if self.current_key != self.session.sequence.iloc[self.trial_nr]["TargetDigit"]:
            # self.session.display_text(text=prompts.error_notification, color=(1.0, 0.0, 0.0),
            # duration=np.abs(self.session.timer.getTime()))
            pass

        # print too slow warning if response is collected in phase 2
        if self.phase == 2:
            # while self.session.timer.getTime() < 0:
            if any(self.get_events()) or any(self.session.mouse.getPressed()):
                #self.session.display_text(text=prompts.too_slow, color=(1.0, 0.0, 0.0),
                                          #duration=np.abs(self.session.timer.getTime()))  # red warning
                self.session.virtual_response_box[0].lineColor = "red"
                # self.session.win.flip()


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
        self.logger = set_logging_level.set_level(self.settings["logging"]["level"])
        self.test = test
        self.this_block = None
        self.subject_id = int(self.output_str.split("-")[1])
        self.trials = []
        if self.settings["mode"]["record_eeg"]:
            self.port = parallel.ParallelPort(0xCFF8)  # set address of port
        # slab.set_default_level(self.settings["session"]["level"])
        # print(f"Set stimulus level to {slab.sound._default_level}")

    def display_response_box(self):
        for stimulus in self.virtual_response_box:
            stimulus.draw()

    def set_block(self, block):
        self.blockdir = os.path.join(self.settings["filepaths"]["sequences"], f"{self.output_str}_block_{block}")
        self.display_text(text=f"Initialisiere Block {block+1} von insgesamt {max(self.blocks)+1}... ",
                          duration=3.0)
        self.this_block = block

    def load_sequence(self):
        self.sequence = pd.read_excel(self.blockdir + ".xlsx")

    def create_trials(self, n_trials, durations, timing='seconds'):
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
            sound_path = os.path.join(trial.session.blockdir, f"s_{trial_nr}.wav")  # s_0, s_1, ... .wav
            #trial.stim = Sound(sound_path)
            trial.stim = Sound(filename=sound_path, device=self.settings["soundconfig"]["device"],
                               mul=self.settings["soundconfig"]["mul"]) #TODO: eventually change this to psychopy sound
            # trial.stim = slab.Binaural.read(sound_path)
            self.trials.append(trial)

    def run(self):
        self.send_trigger("experiment_onset")
        # welcome the participant
        self.display_text(text=prompts.welcome1, keys="space")
        self.display_text(text=prompts.welcome2, keys="space")
        if self.settings["mode"]["camera"]:
            self.display_text(text=prompts.camera_calibration, keys="space")
            self.default_fix.draw()
            self.win.flip()
            self.send_trigger("camera_calibration_onset")
            core.wait(10)
            self.send_trigger("camera_calibration_offset")
        if self.test:
            self.display_text(text=prompts.testing, keys="space")
            self.set_block(block=1)  # intentionally choose block within
            self.load_sequence()
            self.create_trials(n_trials=15,
                               durations=[self.settings["session"]["stimulus_duration"],
                                          self.settings["session"]["response_duration"],
                                          None],
                               timing=self.settings["session"]["timing"])
            self.start_experiment()
            for trial in self.trials:
                self.send_trigger("trial_onset")
                trial.trigger_name = f'Target-{int(trial.parameters["TargetLoc"])}-Singleton-{int(trial.parameters["SingletonLoc"])}-{PRIMING[trial.parameters["Priming"]]}'
                trial.run()
                self.send_trigger("trial_offset")
        else:
            self.start_experiment()
            self.display_text("Drücke LEERTASTE, um zu beginnen.", keys="space")
            for block in self.blocks:
                self.send_trigger("block_onset")
                self.set_block(block=block)
                self.load_sequence()
                self.create_trials(n_trials=self.n_trials,
                                   durations=[self.settings["session"]["stimulus_duration"],
                                              self.settings["session"]["response_duration"],
                                              None],  # this is hacky and usually not recommended (for ITI Jitter)
                                   timing=self.settings["session"]["timing"])
                for trial in self.trials:
                    # make sure the default is black line color
                    self.send_trigger("trial_onset")
                    trial.trigger_name = f'Target-{int(trial.parameters["TargetLoc"])}-Singleton-{int(trial.parameters["SingletonLoc"])}-{PRIMING[trial.parameters["Priming"]]}'
                    trial.run()
                    self.send_trigger("trial_offset")
                self.save_data()
                self.plot_frame_intervals()
                self.send_trigger("block_offset")
                if not block == max(self.blocks):
                    self.display_text(text=prompts.pause, keys="space")
        self.display_text(text=prompts.end, keys="q")
        self.send_trigger("experiment_offset")

    # Function to send trigger value by specifying event name
    def send_trigger(self, event_name):
        if self.settings["mode"]["record_eeg"]:
            # get corresponding trigger value:
            trigger_value = EEG_TRIGGER_MAP[event_name]
            # send trigger to EEG:
            self.port.setData(trigger_value)
            core.wait(0.003)  # TODO: is 3 ms enough?
            # turn off EEG trigger
            self.port.setData(0)
        else:
            pass


if __name__ == '__main__':
    # DEBUGGING
    sess = SpaceprimeSession(output_str='sub-99', output_dir="logs", settings_file="config.yaml")
    # sess.display_text(text=prompts.testing, keys="space")
    sess.set_block(block=1)  # intentionally choose block within
    sess.load_sequence()
    sess.create_trials(n_trials=15,
                       durations=[sess.settings["session"]["stimulus_duration"],
                                  sess.settings["session"]["response_duration"],
                                  None],
                       timing=sess.settings["session"]["timing"])
    sess.start_experiment()
    sess.display_response_box()
    sess.win.flip()

    while True:
        # Handle mouse clicks
        for i, stimulus in enumerate(sess.virtual_response_box):  # skip the rectangle (i==0)
            if i == 0:
                continue
            if stimulus.contains(sess.mouse):
                print("Mouse position recognized")
                stimulus.color = "red"

                # sess.win.callOnFlip(change_color)  # Schedule color change for next flip
                # show feedback by digit color change

            # sess.mouse.clickReset()  # Update mouse position
            # sess.win.flip()  # Flip the window to display any changes
        event = psychopy.event.getKeys()
        if len(event) > 0:
            sess.win.close()
            break
    #time.sleep(5)
    # sess.win.close()
