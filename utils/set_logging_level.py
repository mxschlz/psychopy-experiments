from psychopy import logging


def set_level(level):
    if level == "DEBUG":
        logging.console.setLevel(logging.DEBUG)
        return dict(level=logging.DEBUG)
    elif level == "INFO":
        logging.console.setLevel(logging.INFO)
        return dict(level=logging.INFO)
    elif level == "WARNING":
        logging.console.setLevel(logging.WARNING)
        return dict(level=logging.WARNING)
    elif level == "ERROR":
        logging.console.setLevel(logging.ERROR)
        return dict(level=logging.ERROR)
    elif level == "CRITICAL":
        print("Critical logging level not supported by Psychopy.")
    elif level == "DATA":
        logging.console.setLevel(logging.DATA)
        return dict(level=logging.DATA)
    elif level == "EXP":
        logging.console.setLevel(logging.EXP)
        return dict(level=logging.EXP)

    print(f"Set logging level to {level}.")
