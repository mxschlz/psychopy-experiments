# -*- coding: utf-8 -*-
"""
PsychoPy Key Name Tester Script
===============================

This script helps you identify the names that PsychoPy assigns to key presses
on different operating systems (Windows and macOS), especially for the
numeric keypad.

Instructions:
1.  Copy and paste this entire code into the PsychoPy Coder view.
2.  Run the script.
3.  A window will appear. Follow the instructions on the screen.
4.  Press various keys, focusing on the numeric keypad (both with and
    without Num Lock if applicable on Windows).
5.  The name PsychoPy uses for the last key(s) you pressed will appear
    in the center of the screen.
6.  Note down these names, especially how they differ between your Windows
    and Mac machines.
7.  Press the 'escape' key to quit the script.
"""

from psychopy import visual, core, event

# --- Setup ---
# Create a window to draw on
win = visual.Window(
    size=[800, 600],  # Feel free to adjust size
    fullscr=False,     # Set to True for fullscreen, False for windowed
    screen=0,
    winType='pyglet', # You can try 'ptb' if 'pyglet' gives issues
    allowGUI=True,
    allowStencil=False,
    monitor='testMonitor',
    color=[0,0,0],      # Black background
    colorSpace='rgb',
    blendMode='avg',
    useFBO=True,
    units='height'
)

# Text stimulus for instructions
instructions_text = visual.TextStim(
    win=win,
    text="Press any key (especially numeric keypad keys).\n\n"
         "The name PsychoPy sees will appear below.\n\n"
         "Press 'escape' to quit.",
    pos=(0, 0.25),  # Positioned towards the top
    height=0.04,
    wrapWidth=None,
    ori=0,
    color='white',
    colorSpace='rgb',
    opacity=1,
    languageStyle='LTR',
    depth=0.0
)

# Text stimulus to display the key pressed
key_display_text = visual.TextStim(
    win=win,
    text="Waiting for key press...",
    pos=(0, -0.1), # Positioned in the center/below instructions
    height=0.08,  # Make it larger for easy reading
    wrapWidth=None,
    ori=0,
    color='lime', # Green color for visibility
    colorSpace='rgb',
    opacity=1,
    languageStyle='LTR',
    depth=-1.0
)

# --- Main Loop ---
keep_running = True
while keep_running:
    # --- Draw stimuli ---
    instructions_text.draw()
    key_display_text.draw()
    win.flip() # Update the screen

    # --- Check for key presses ---
    # getKeys() returns a list of keys pressed since the last check.
    # We set keyList=None to get all keys. We set timeStamped=False for simplicity.
    keys_pressed = event.getKeys(keyList=None, timeStamped=False)

    # --- Process key presses ---
    if keys_pressed:
        # If any key was pressed, update the display text.
        # We join the list with commas in case multiple keys were pressed
        # very quickly (though usually it will be one).
        key_display_text.setText(str(keys_pressed))

        # Check if 'escape' was pressed to end the script
        if 'escape' in keys_pressed:
            keep_running = False

    # A small pause to prevent the script from using 100% CPU
    # You might not need this in a real experiment loop with stimuli timing.
    core.wait(0.01)

# --- Cleanup ---
win.close()
core.quit()

print("Script finished.")