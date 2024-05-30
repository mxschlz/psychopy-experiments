import os
import sys

# Get the absolute path of the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory (or its parent) to the system path
sys.path.append(script_dir)

# Now you can import your project's modules
# from my_module import my_function

print("Script directory added to sys.path:", script_dir)

