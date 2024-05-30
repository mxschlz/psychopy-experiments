import yaml
import sys
import os


# append to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)


try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


stream = open("example_config.yaml", 'r')
dictionary = yaml.load(stream, Loader)
for key, value in dictionary.items():
    print(key + " : " + str(value))

print(dictionary["window"]["window_size"])
print(type(dictionary["stimuli_fp"]))
