import sounddevice as sd
import numpy as np
import time
import os
from scipy.io import wavfile

# ==============================================================================
# 1. Configuration - CHANGE THIS LINE
# ==============================================================================
# NOTE: Replace this placeholder with the actual path to your .wav file.
# The file is loaded ONLY for its sample rate and channel count information.
AUDIO_FILE_PATH = "D:\\MSchulz\\SPACECUE_implicit\\sequences\\sci-999_block_0\\s_1.wav"
# FACTOR: Increase the volume to rule out very faint playback. (e.g., 1.5 = 50% boost)
VOLUME_BOOST_FACTOR = 0.1
# ==============================================================================

# List of Host APIs to test if default playback fails
# ASIO is included as it is the standard for professional interfaces like RME Fireface.
HOST_APIS = ['ASIO', 'MME', 'DirectSound', 'WASAPI']


def load_audio_file(file_path):
    """Loads a WAV file to determine sample rate and channel count."""
    if not os.path.exists(file_path):
        print(f"ERROR: Audio file not found at: {file_path}")
        print("Please update the AUDIO_FILE_PATH variable.")
        return None, None

    try:
        # We only need metadata, but wavfile.read loads the data too.
        sample_rate, audio_data = wavfile.read(file_path)

        # Ensure it's 2D for mono/stereo/multi-channel compatibility
        if audio_data.ndim == 1:
            audio_data = audio_data[:, np.newaxis]

        print(f"Successfully loaded file metadata: {os.path.basename(file_path)}")
        print(f"Sample Rate: {sample_rate} Hz, Channels: {audio_data.shape[1]}")

        if audio_data.shape[1] != 3:
            print(
                "WARNING: Audio file does not have 3 channels as expected. Test will proceed with 3-channel test tone.")

        return sample_rate, audio_data.shape[1]  # Return only samplerate and channel count

    except Exception as e:
        print(f"ERROR loading audio file metadata: {e}")
        return None, None


def generate_test_signal(sample_rate, duration_seconds=2):
    """Generates a 3-channel sine wave test signal."""
    required_channels = 3
    t = np.linspace(0., duration_seconds, int(sample_rate * duration_seconds), endpoint=False)

    # Channel 1: Low Tone (440 Hz)
    c1 = np.sin(2. * np.pi * 440. * t)

    # Channel 2: Mid Tone (880 Hz)
    c2 = np.sin(2. * np.pi * 880. * t)

    # Channel 3: High Tone (1760 Hz)
    c3 = np.sin(2. * np.pi * 1760. * t)

    # Combine channels and apply volume boost
    audio_data = np.stack([c1, c2, c3], axis=1).astype(np.float32)
    audio_data = np.clip(audio_data * VOLUME_BOOST_FACTOR, -1.0, 1.0)

    print(f"Generated 3-Channel Test Tone ({duration_seconds}s). VOLUME BOOST: {VOLUME_BOOST_FACTOR}x")
    return audio_data


def try_playback(audio_data, sample_rate, dev_id, channels_for_check, api_name=None, test_type="Native"):
    """
    Attempts playback with specific channel count and returns status/message.
    'channels_for_check' is the number of channels the driver is expected to handle.
    """

    required_channels = audio_data.shape[1]

    # Determine the device argument for sd.play()
    if api_name:
        device_arg = (dev_id, api_name)
    else:
        device_arg = dev_id

    api_display_name = api_name or 'Default API'

    try:
        # Check settings using the expected number of channels
        if api_name is None or api_name == 'ASIO':
            sd.check_output_settings(
                device=dev_id,
                samplerate=sample_rate,
                channels=channels_for_check
            )

        # Play the sound: The channel count is defined by audio_data.shape[1]
        sd.play(audio_data, samplerate=sample_rate, device=device_arg)
        sd.wait()

        # Define status based on test type
        if test_type == "Native":
            status = "SUCCESS" if api_name is None else f"API_SUCCESS({api_name})"
        elif test_type == "Padded":
            status = "FALLBACK SUCCESS" if api_name is None else f"API_SUCCESS_PADDED({api_name})"
        elif test_type == "Shifted":
            status = "SHIFTED SUCCESS" if api_name is None else f"API_SUCCESS_SHIFTED({api_name})"

        message = f"Sound played successfully on {required_channels} stream channels using {api_display_name}."
        time.sleep(0.5)

    except sd.PortAudioError as e:
        status = "FAILED" if api_name is None else f"API_FAILED({api_name})"
        error_message = e.args[0].strip()[:60] if e.args else "Unknown PortAudio Error"
        message = f"Config Error ({api_display_name}): {error_message}..."
    except Exception as e:
        status = "FAILED" if api_name is None else f"API_FAILED({api_name})"
        message = f"Unexpected Error ({api_display_name}): {e}"

    return status, message


def test_audio_devices(sample_rate, required_channels):
    """Iterates through all output devices and attempts to play the test tone."""

    # 1. Generate the guaranteed 3-channel test tone
    audio_tone = generate_test_signal(sample_rate)

    # 2. Get all available devices
    devices = sd.query_devices()
    output_devices = [d for i, d in enumerate(devices) if d['max_output_channels'] > 0]

    print("\n" + "=" * 70)
    print(f"Found {len(output_devices)} potential output device(s).")
    print(f"Starting test for audio with {required_channels} channel(s) using SINE WAVES.")
    print("=" * 70)

    for device in output_devices:
        dev_id = device['index']
        name = device['name']
        max_channels = device['max_output_channels']

        print(f"\n[DEVICE {dev_id}] {name} (Max Channels: {max_channels})")

        # --- Attempt 1: Native 3-Channel Stream (Default API) ---
        if required_channels > max_channels:
            status = "SKIP"
            message = f"Audio channels ({required_channels}) exceed device's max channels ({max_channels})."
            print(f"  -> [SKIP] - {message}")
            continue

        print("  -> Testing Native 3-Channel Stream (Default API)...", end="", flush=True)
        status, message = try_playback(audio_tone, sample_rate, dev_id, required_channels)
        print(f" -> [{status}] - {message}")

        if status.startswith("SUCCESS"):
            continue

            # --- Prepare for 4-Channel Fallbacks ---
        if required_channels == 3 and max_channels >= 4:
            # Padded: [C1, C2, C3_tone, Silent] (Original padding)
            silent_channel = np.zeros((audio_tone.shape[0], 1), dtype=audio_tone.dtype)
            audio_padded = np.concatenate((audio_tone, silent_channel), axis=1)

            # Shifted: [C1, C2, Silent, C3_tone] (New padding to skip channel 3)
            # Split audio_tone into C1/C2 (index 0:2) and C3 (index 2:3)
            audio_c1_c2 = audio_tone[:, :2]
            audio_c3 = audio_tone[:, 2:3]
            audio_shifted = np.concatenate((audio_c1_c2, silent_channel, audio_c3), axis=1)

            # --- Attempt 2: 4-Channel Padded Stream (Default API) ---
            print("  -> Testing FALLBACK: 4-Channel Padded Stream [C1, C2, C3, S] (Default API)...", end="", flush=True)
            status_fb, message_fb = try_playback(audio_padded, sample_rate, dev_id, 4, test_type="Padded")
            print(f" -> [{status_fb}] - {message_fb}")
            if status_fb.startswith("FALLBACK SUCCESS"):
                continue

            # --- Attempt 3: 4-Channel Shifted Stream (Default API) ---
            print("  -> Testing SHIFTED: 4-Channel Shifted Stream [C1, C2, S, C3] (Default API)...", end="", flush=True)
            status_shift, message_shift = try_playback(audio_shifted, sample_rate, dev_id, 4, test_type="Shifted")
            print(f" -> [{status_shift}] - {message_shift}")
            if status_shift.startswith("SHIFTED SUCCESS"):
                continue

        # --- Attempt 4: Host API Fallback Testing ---
        # Only run if no success was found so far
        if not (status.startswith("SUCCESS") or status_fb.startswith("SUCCESS") or status_shift.startswith("SUCCESS")):
            print("\n  -> Starting Host API Fallback Tests...")

            API_SUCCESS = False
            for api_name in HOST_APIS:
                if API_SUCCESS: break  # Stop testing if any API succeeds

                # Test 3-channel native stream with explicit API
                status_api_3, message_api_3 = try_playback(audio_tone, sample_rate, dev_id, required_channels,
                                                           api_name=api_name, test_type="Native")
                print(f"    -> {api_name} (3 CH Native): [{status_api_3}]")
                if status_api_3.startswith("API_SUCCESS"):
                    API_SUCCESS = True
                    break

                # Test 4-channel padded stream with explicit API (if padding was applicable)
                if required_channels == 3 and max_channels >= 4:
                    # Original Padding: [C1, C2, C3, Silent]
                    status_api_4_padded, message_api_4_padded = try_playback(audio_padded, sample_rate, dev_id, 4,
                                                                             api_name=api_name, test_type="Padded")
                    print(f"    -> {api_name} (4 CH Padded): [{status_api_4_padded}]")
                    if status_api_4_padded.startswith("API_SUCCESS_PADDED"):
                        API_SUCCESS = True
                        break

                    # Shifted Padding: [C1, C2, Silent, C3]
                    status_api_4_shifted, message_api_4_shifted = try_playback(audio_shifted, sample_rate, dev_id, 4,
                                                                               api_name=api_name, test_type="Shifted")
                    print(f"    -> {api_name} (4 CH Shifted): [{status_api_4_shifted}]")
                    if status_api_4_shifted.startswith("API_SUCCESS_SHIFTED"):
                        API_SUCCESS = True
                        break

    print("\n" + "=" * 70)
    print("Device testing complete.")
    print("=" * 70)


if __name__ == "__main__":

    # 1. Load the audio file metadata
    fs, required_ch = load_audio_file(AUDIO_FILE_PATH)

    if fs is not None and required_ch is not None:
        # 2. Run the test
        test_audio_devices(fs, required_ch)

    print("\n" + "#" * 70)
    print("CRITICAL TROUBLESHOOTING: DIAGNOSIS TIME")
    print("We are now using a 3-channel test tone (Low, Mid, High frequencies) to eliminate the WAV file as the cause.")
    print("\nIf you only see SW Playback 1 & 2 active in TotalMix FX:")
    print("   -> Your RME driver/API combination is truncating the stream to 2 channels.")
    print("   -> **SOLUTION:** You MUST use the **4-channel SHIFTED PADDING** array in your final code.")
    print("\nIf you see SW Playback 1, 2, & 3 active in TotalMix FX:")
    print("   -> The Python stream is correct. The problem is your original WAV file has silent data on Channel 3.")
    print("\nTotalMix Routing Checklist (AN 3, 4, 5 assumed):")
    print("1. **UNLINK** AN 3/4 and AN 5/6 (Right-Click > Stereo Link OFF).")
    print("2. Set AN 3 receives ONLY SW 1, AN 4 receives ONLY SW 2, AN 5 receives ONLY SW 3.")
    print("#" * 70)

    # Print the default device info at the end for reference
    default_output_device = sd.default.device[1]
    default_device_info = sd.query_devices(default_output_device)
    print("\nDefault Output Device (as per system/sounddevice config):")
    print(f"  Index: {default_output_device}")
    print(f"  Name: {default_device_info['name']}")
