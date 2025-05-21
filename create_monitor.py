from psychopy.monitors import Monitor
import yaml


settings = yaml.safe_load(open("SPACECUE/config.yaml", "r"))

monitor = Monitor(**settings["monitor"])
monitor.setSizePix(settings["window"]["size"])
monitor.save()