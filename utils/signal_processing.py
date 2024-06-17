import pickle
import slab
import librosa
import numpy as np


try:
    ils = pickle.load(open('ils.pickle', 'rb'))  # load pickle
    print("Interaural level spectrum found. Loading ... ")
except FileNotFoundError:
    print("Interaural level spectrum could not be found in project. Generating ... ")
    ils = slab.Binaural.make_interaural_level_spectrum()
    print("Saving interaural level spectrum in current working directory ... ")
    pickle.dump(ils, open('../ils.pickle', 'wb'))  # save using pickle
    print("Saving interaural level spectrum is done. Please look in current working directory for ils.pickle! ")


def lateralize(sound, azimuth, ils=ils):
    """
    Creates a lateralized (binaural) version of a monaural sound source.

    This function takes a monaural sound and an azimuth angle, and returns
    a binaural version of the sound with interaural level and time differences
    (ILDs and ITDs) adjusted to simulate the specified azimuth. If a list of
    azimuth angles is provided, a list of corresponding binaural sounds is returned.

    Args:
        sound (slab.Sound): The monaural sound to be lateralized. If the sound is
            already binaural, it will be used as-is for ILD and ITD manipulation.
        azimuth (int): The desired azimuth angle in degrees.
        ils (int, optional): The interaural level spectrum (ILS) in dB/degree
            used for ILD calculation.

    Returns:
        slab.Binaural or list: A binaural version of the input sound with the
            specified azimuth, or a list of binaural sounds if a list of azimuths
            was provided. If the input sound was already binaural, the returned
            sound will have modified ILD and ITD based on the given azimuth.
    """

    if not isinstance(sound, slab.Binaural):
        sound_monaural = sound
        binaural_stim = slab.Binaural(data=sound_monaural.data, samplerate=sound_monaural.samplerate)
    else:
        binaural_stim = sound  # Use the existing binaural sound

    if not isinstance(azimuth, int):
        raise ValueError("Azimuth must be an integer!")
    else:
        ild = binaural_stim.azimuth_to_ild(azimuth, ils=ils)
        itd = binaural_stim.azimuth_to_itd(azimuth)
        stim = binaural_stim.itd(itd).ild(ild)
    return stim


def shift_pitch(sound, pitch_factor):
    """
    Shifts the pitch of a monaural sound by a specified factor.

    This function takes a slab.Sound object and a pitch factor, and returns a
    new slab.Sound object with the pitch shifted. The pitch factor is expressed
    in terms of semitones (1 semitone = 1/12th of an octave).

    If the input sound is binaural (slab.Binaural), this function will print a
    warning message and only process the left channel.

    Args:
        sound (slab.Sound): The sound object to be pitch shifted.
        pitch_factor (float): The amount of pitch shift in semitones.
            Positive values shift the pitch up, negative values shift it down.

    Returns:
        slab.Sound: A new sound object with the pitch shifted.

    Raises:
        ValueError: If the input sound is not a slab.Sound object.
    """

    if isinstance(sound, slab.Binaural):
        if not np.all(sound.data[:, 0] == sound.data[:, 1]):  # Check if channels are different
            print("WARNING: Stimulus seems to be lateralized. This function operates on single channel stimuli only.")
        print("Given stimulus is instance of slab.Binaural! Removing right channel...")
        sound = slab.Sound(data=sound.data[:, 0], samplerate=sound.samplerate)  # Use only left channel

    data = sound.data
    sr = sound.samplerate

    if data.ndim > 1:  # Ensure the data is mono
        data = data[:, 0]  # Take only the first channel

    y_shifted = librosa.effects.pitch_shift(y=data, sr=sr, n_steps=pitch_factor)
    shifted = slab.Sound(data=y_shifted, samplerate=sr)
    return shifted


def modulate_amplitude(sound, modulation_freq):
    """
    Amplitude modulates a monaural sound with a sine wave carrier.

    This function takes a slab.Sound object and a modulation frequency,
    and returns the amplitude modulated signal as a numpy array. It extracts
    the data from the left channel of the sound (assuming monaural input)
    and performs amplitude modulation using a sine wave carrier with the
    specified frequency.

    Args:
        sound (slab.Sound): The sound object to be amplitude modulated.
            If the sound is binaural, it will only modulate the left channel.
        modulation_freq (float): The frequency (in Hz) of the modulating sine wave.

    Returns:
        numpy.ndarray: The amplitude modulated signal as a 1D numpy array.
    """
    if isinstance(sound, slab.Binaural):
        print("WARNING: Input sound is binaural. Only the left channel will be modulated.")
    y = sound.data[:, 0]  # Extract data from the left channel (assuming monaural)
    sr = sound.samplerate

    # Calculate duration and time array
    duration = sound.duration
    t = np.linspace(0, duration, len(y), endpoint=False)

    # Generate carrier sine wave
    carrier = np.sin(2 * np.pi * modulation_freq * t)

    # Perform amplitude modulation
    y_modulated = y * carrier

    return slab.Sound(data=y_modulated, samplerate=sr)


def externalize(sound, azi, ele):
    """
    Convolves a sound with a head-related transfer function (HRTF) to create
    a spatially localized sound.

    This function takes a slab.Sound object, an azimuth angle, and an elevation
    angle, and returns a new slab.Binaural object with the sound convolved with
    the corresponding KEMAR HRTF.

    Args:
        sound (slab.Sound): The sound object to be spatialized.
        azi (int): The azimuth angle of the desired sound location in degrees.
        ele (int): The elevation angle of the desired sound location in degrees.

    Returns:
        slab.Binaural: A binaural sound object with the input sound convolved
            with the KEMAR HRTF for the specified azimuth and elevation.

    Raises:
        ValueError: If the specified azimuth and elevation combination is not
            found in the KEMAR HRTF.
    """
    if azi > 0:
        azi = azi + 180
    if azi < 0:
        azi = abs(azi)
    hrtf = slab.HRTF.kemar()  # Load the KEMAR HRTF
    idx = np.where((hrtf.sources.vertical_polar[:, 0] == azi) & (hrtf.sources.vertical_polar[:, 1] == ele))[0]
    if not idx.size:  # idx is empty
        raise ValueError(f'No azimuth {azi}°, elevation {ele}° found in HRTF.')
    return hrtf.apply(idx[0], sound)  # Apply the HRTF to the sound


if __name__ == '__main__':
    # load up sound
    input_file = "C:\\PycharmProjects\\psychopy-experiments\\stimuli\\digits_all_250ms\\1.wav"
    sound = slab.Sound.read(input_file)

    # coordinates
    azi = [-90, -45, 0, 45, 90]
    ele = 0

    # externalize
    for az in azi:
        ext = externalize(sound, azi=az, ele=ele)
        ext.play()

    # shift pitch
    pitch_factor = 10
    pitched = shift_pitch(ext, pitch_factor)

    # modulate amplitude
    modulated = modulate_amplitude(sound, modulation_freq=30)

    # lateralize at given azimuth
    lagged = lateralize(sound, azimuth=azi)
