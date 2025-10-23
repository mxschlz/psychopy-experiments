import sounddevice as sd
import soundfile as sf
import os
os.environ["SD_ENABLE_ASIO"] = "1"


# add 15 dB to the 50 dB sounds so that we get to 65 dB
mul = 15
# define soundpath for sound files
soundpath = "D:\MSchulz\SPACECUE_implicit\sequences\sci-999_block_0"
arrays = []
stream = sd.OutputStream(samplerate=44100, channels=3, blocksize=None, latency="low", device=10, dtype="float32")
# start stream
stream.start()

# play all sounds in that soundpath
for sound_path in os.listdir(soundpath):
    data, sr = sf.read(os.path.join(soundpath, sound_path), dtype='float32')
    data = data * (10 ** (mul / 20))  #  apply dB to the data array
    arrays.append(data)
    stream.write(data)  # play sound
