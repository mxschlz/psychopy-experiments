import sys


class Sound(object):
	'''
	class for playing low-latency sound on all platforms
	'''

	def __init__(self, filename='', device=None, mul=1):
		'''
		filename: a sound file supported by libsndfile
		device: portaudio device used for playback
		check for devices by running python -m sounddevice
		or sounddevice.query_devices()
		mul: volume multiplier
		'''
		self.filename = filename
		if filename == '':
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
		self.data, self.sr = sf.read(filename, dtype='float32')
		self.data = self.data * (10 ** (mul / 20))

		self.duration = self.data.shape[0] / self.sr
		self._isPlaying = False
		self._isFinished = False

	@property
	def isPlaying(self):
		"""`True` if the audio playback is ongoing."""
		return self._isPlaying

	@property
	def isFinished(self):
		"""`True` if the audio playback has completed."""
		return self._isFinished

	def getDuration(self):
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

