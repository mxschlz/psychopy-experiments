import sys


class SoundDeviceSound(object):
	'''
	class for playing low-latency sound on all platforms
	'''

	def __init__(self, filename='', device=None, mul=1, data=None, sr=None):
		'''
		filename: a sound file supported by libsndfile
		device: portaudio device used for playback
		check for devices by running python -m sounddevice
		or sounddevice.query_devices()
		mul: volume multiplier
		'''
		self.filename = filename
		if filename == '' and data is None:
			print
			'no filename specified'
			sys.exit()

		# check if filename exists

		self.too_high_vol_txt = 'volume attentuation by more than 120dB not useful'
		if mul > 120:
			print(self.too_high_vol_txt)
			sys.exit()

		self.device = device
		try:
			sf = __import__('soundfile')
		except ImportError:
			print('soundfile Module missing, but it is necessary for sound playback')
			sys.exit()
		try:
			self.sd = __import__('sounddevice')
		except ImportError:
			print('sounddevice module missing, but it is necessary for sound playback')
			sys.exit()
		if isinstance(filename, str) and data is None:
			self.data, self.sr = sf.read(filename, dtype='float32')
		elif data is not None:
			self.data = data
		if sr is not None:
			self.sr = sr
		self.data = self.data * (10 ** (mul / 20))

		self.duration = self.data.shape[0] / self.sr
		self._isPlaying = False
		self._isFinished = False

	def is_playing(self):
		"""`True` if the audio playback is ongoing."""
		return self._isPlaying

	def is_finished(self):
		"""`True` if the audio playback has completed."""
		return self._isFinished

	def get_duration(self):
		return self.duration

	def play(self, **kwargs):
		self._isPlaying = True
		self._isFinished = False
		self.sd.play(data=self.data, samplerate=self.sr, device=self.device, **kwargs)

	def stop(self):
		self._isPlaying = False
		self._isFinished = True
		self.sd.stop()

	def wait(self):
		self._isPlaying = False
		self.sd.wait()

	def change_volume(self, mul=1):
		if mul > 120:
			print(self.too_high_vol_txt)
		else:
			self.data = self.data * (10 ** (mul / 20))


if __name__ == "__main__":
	sound = SoundDeviceSound(filename='C:\\PycharmProjects\\psychopy-experiments\\stimuli\\digits_all_250ms\\1.wav')
	while True:
		if not sound.isPlaying():
			sound.play()