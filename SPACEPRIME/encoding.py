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
    "block_onset": 1,
    "start_experiment": 2,
    "end_experiment": 3,
    "response": 4,
    "lol": 5
}