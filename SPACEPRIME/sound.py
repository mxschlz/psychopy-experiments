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
			print
			self.too_high_vol_txt
			sys.exit()

		self.device = device
		try:
			sf = __import__('soundfile')
		except ImportError:
			print
			'soundfile Module missing, but it is necessary for sound playback'
			sys.exit()
		try:
			self.sd = __import__('sounddevice')
		except ImportError:
			print
			'sounddevice module missing, but it is necessary for sound playback'
			sys.exit()
		self.data, self.sr = sf.read(filename, dtype='float32')
		self.data = self.data * (10 ** (-mul / 20))

		self.duration = self.data.shape[0] / self.sr

	def getDuration(self):
		return self.duration

	def play(self):
		self.sd.play(self.data, self.sr, device=self.device)

	def change_volume(self, mul=1):
		if mul > 120:
			print
			self.too_high_vol_txt
		else:
			self.data = self.data * (10 ** (-mul / 20))

