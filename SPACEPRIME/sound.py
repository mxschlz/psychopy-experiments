import sys


class SoundDeviceSound(object):
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


class WinSound(object):
    """
    A windows-only low-latency replacement for psychopy.sound.
    It can only play wav files. Timing is unreliable if sound.play() is called
    before previous sound ends. Usage::

        beep = ppc.Sound('beep.wav')
        beep.play()

        # or generated beep:
        beep = ppc.Sound()
        beep.beep(1000, 0.2)  # 1000 Hz for 0.2 seconds
    """
    def __init__(self, filename=''):
        """ :filename: a .wav file"""
        self.sound = filename
        self._winsound = __import__('winsound')

    def play(self):
        """ plays the sound file with low latency"""
        self._winsound.PlaySound(self.sound,  self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)

    def beep(self, frequency, duration):
        """ plays a beep with low latency"""
        self._winsound.Beep(frequency, duration / float(1000))