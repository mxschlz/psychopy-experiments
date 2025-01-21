# encoder contains coordinates in azi, ele
SPACE_ENCODER = {
    1: (-90, 0),
    2: (0, 0),
    3: (90, 0)
}

RESPONSE_ENCODER = {
    "end": 1,
    "down": 2,
    "pagedown": 3,
    "left": 4,
    "right": 6,
    "home": 7,
    "up": 8,
    "pageup": 9
}

EEG_TRIGGER_MAP = {
    "test_trigger": 1,
    "camera_calibration_onset": 2,
    "camera_calibration_offset": 3,
    "block_onset": 4,
    "block_offset": 5,
    "experiment_onset": 6,
    "experiment_offset": 7,
    "trial_onset": 8,
    "trial_offset": 9,
    "Target-1-Singleton-0-C": 10,
    "Target-1-Singleton-2-C": 12,
    "Target-1-Singleton-3-C": 13,
    "Target-1-Singleton-0-PP": 110,
    "Target-1-Singleton-2-PP": 112,
    "Target-1-Singleton-3-PP": 113,
    "Target-1-Singleton-0-NP": 210,
    "Target-1-Singleton-2-NP": 212,
    "Target-1-Singleton-3-NP": 213,
    "Target-2-Singleton-0-C": 20,
    "Target-2-Singleton-1-C": 21,
    "Target-2-Singleton-3-C": 23,
    "Target-2-Singleton-0-PP": 120,
    "Target-2-Singleton-1-PP": 121,
    "Target-2-Singleton-3-PP": 123,
    "Target-2-Singleton-0-NP": 220,
    "Target-2-Singleton-1-NP": 221,
    "Target-2-Singleton-3-NP": 223,
    "Target-3-Singleton-0-C": 30,
    "Target-3-Singleton-1-C": 31,
    "Target-3-Singleton-2-C": 32,
    "Target-3-Singleton-0-PP": 130,
    "Target-3-Singleton-1-PP": 131,
    "Target-3-Singleton-2-PP": 132,
    "Target-3-Singleton-0-NP": 230,
    "Target-3-Singleton-1-NP": 231,
    "Target-3-Singleton-2-NP": 232,
}

PRIMING = {
    0: "C",
    1: "PP",
    -1: "NP"
}

FLANKER_MAP = {
    "congruent_left": 240,
    "congruent_right": 241,
    "incongruent_left": 243,
    "incongruent_right": 244,
    "neutral_left": 245,
    "neutral_right": 246,
    "none": 250
}

PASSIVE_MAP = {

}