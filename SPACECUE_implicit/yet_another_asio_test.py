import os

# 💡 Step 1: Set the environment variable to enable ASIO support
os.environ["SD_ENABLE_ASIO"] = "1"

# 💡 Step 2: Now import sounddevice
import sounddevice as sd
import numpy as np

# --- Verify the Driver is Now Visible ---
print("Available Host APIs:")
print(sd.query_hostapis())

print("\nAvailable Devices:")
print(sd.query_devices())

# Look in the output for a Host API named 'ASIO' and your drivers
# 'ASIO4ALL v2' or 'FlexASIO'.

# --- Configure and Play 3-Channel Audio ---
# You'll need to know the index of your desired ASIO device.
ASIO_DEVICE_INDEX = 5  # <--- REPLACE with the correct index found above

sd.default.device = ASIO_DEVICE_INDEX
sd.default.channels = 3  # Set to 3 channels for output
sd.default.samplerate = 48000  # Set your desired sample rate

# Create a sample 3-channel (stereo + one extra) signal
# Shape is (samples, channels)
samplerate = sd.default.samplerate
duration = 2  # seconds
t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
signal = np.zeros((len(t), 3), dtype=np.float32)

# Channel 1: Sine wave
signal[:, 0] = np.sin(2. * np.pi * 440 * t)
# Channel 2: Sawtooth wave
signal[:, 1] = np.linspace(-1, 1, len(t))
# Channel 3: Square wave
signal[:, 2] = np.sign(np.sin(2. * np.pi * 220 * t))

print(f"\nPlaying {sd.default.channels} channels via {sd.query_devices(ASIO_DEVICE_INDEX)['name']}...")
sd.play(signal)
sd.wait()