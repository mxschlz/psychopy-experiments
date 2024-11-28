import os

_thisDir = os.path.dirname(os.path.abspath(__file__))

print("Working directory: ", _thisDir)
os.chdir(_thisDir)
