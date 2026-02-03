from psychopy import visual, core, event

# 💡 ENSURE these indices match the successful setup from Section 2
MAIN_SCREEN_INDEX = 1
LAB_SCREEN_INDEX = 0

main_win = visual.Window(size=[1920, 1080], fullscr=True, screen=MAIN_SCREEN_INDEX, color='black')
mirror_win = visual.Window(size=[800, 600], fullscr=False, screen=LAB_SCREEN_INDEX, color='white')

# Create one stimulus object
stim_text = visual.TextStim(main_win, text="Trial 1", color='white')
stim_clock = core.Clock()

print("Running mirroring test. Press 'q' or ESC to quit.")

while 'q' not in event.getKeys() and 'escape' not in event.getKeys():
    # Update stimulus properties
    current_time = stim_clock.getTime()
    stim_text.text = f"Time: {current_time:.2f}s"

    # 1. Draw to the MAIN window
    stim_text.draw()
    main_win.flip()

    # 2. Draw the SAME stimulus to the MIRROR window
    # Temporarily set the stimulus to use the mirror window
    stim_text.win = mirror_win
    stim_text.draw()
    mirror_win.flip()

    # Reset the stimulus back to the main window for the next iteration
    stim_text.win = main_win

    # Check for quit events across all open windows
    event.getKeys()

    # Simulate a short trial duration
    core.wait(0.05)

# Clean up
main_win.close()
mirror_win.close()
core.quit()