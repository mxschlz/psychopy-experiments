from psychopy import logging


def set_level(level):
    if level == "DEBUG":
        logging.console.setLevel(logging.DEBUG)
    elif level == "INFO":
        logging.console.setLevel(logging.INFO)
    elif level == "WARNING":
        logging.console.setLevel(logging.WARNING)
    elif level == "ERROR":
        logging.console.setLevel(logging.ERROR)
    elif level == "CRITICAL":
        print("Critical logging level not supported by Psychopy.")
    elif level == "DATA":
        logging.console.setLevel(logging.DATA)
    elif level == "EXP":
        logging.console.setLevel(logging.EXP)

    print(f"Set logging level to {level}.")
