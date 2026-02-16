import os
from gtts import gTTS
from pydub import AudioSegment
from pydub.silence import detect_leading_silence


def speed_change(sound, speed=1.5):
    # Changes speed without affecting pitch
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


# Configuration
speed_factor = 1.0  # Slightly fast but still very clear
target_sample_rate = 44100
output_dir = "C:\\Users\\Max\\PycharmProjects\\psychopy-experiments\\SPACECUE_implicit\\stimuli\\letters"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
           'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
           'Ä', 'Ö', 'Ü', 'ß']

print(f"Generating audio at {target_sample_rate}Hz...")

for char in letters:
    temp_file = "temp.mp3"
    tts = gTTS(text=char, lang='de')
    tts.save(temp_file)

    # 1. Load and convert to target sample rate immediately
    audio = AudioSegment.from_mp3(temp_file).set_frame_rate(target_sample_rate)

    # 2. Trim leading silence for precise ERP triggering
    start_trim = detect_leading_silence(audio)
    audio = audio[start_trim:]

    # 3. Apply speed increase
    fast_audio = speed_change(audio, speed=speed_factor)

    # 4. Peak Normalize to -1.0 dB (Ensures consistent loudness)
    normalized_audio = fast_audio.apply_gain(-1.0 - fast_audio.max_dBFS)

    # 5. Export as high-quality WAV
    name = char if char != 'ß' else 'eszett'
    file_path = os.path.join(output_dir, f"{name}.wav")
    normalized_audio.export(file_path, format="wav", parameters=["-ar", str(target_sample_rate)])

    print(f"Exported: {name}.wav | Sample Rate: {normalized_audio.frame_rate}Hz")

if os.path.exists(temp_file):
    os.remove(temp_file)

print("\nDone! All files are normalized and set to 44.1kHz.")