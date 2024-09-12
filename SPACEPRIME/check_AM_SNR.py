import os
import slab
import numpy as np
import matplotlib.pyplot as plt
from utils.signal_processing import modulate_amplitude
plt.ion()


# load sounds
singletons = [slab.Sound.read(f"stimuli/distractors_high/{x}")
              for x in os.listdir(f"stimuli/distractors_high")]
targets = [slab.Sound.read(f"stimuli/targets_low_30_Hz/{x}") for x in os.listdir(f"stimuli/targets_low_30_Hz")]
others = [slab.Sound.read(f"stimuli/digits_all_250ms/{x}") for x in
          os.listdir(f"stimuli/digits_all_250ms")]
targets_new = [modulate_amplitude(x, modulation_freq=30) for x in others]

# get all rms for stimuli
rms_targets = [np.sqrt(np.mean(x ** 2, axis=0)) for x in targets]
rms_others = [np.sqrt(np.mean(x ** 2, axis=0)) for x in others]
rms_targets_new = [np.sqrt(np.mean(x ** 2, axis=0)) for x in targets_new]
# Calculate normalization factors
normalization_factors = [rms_others[i] / rms_targets[i] for i in range(len(rms_others))]
# Apply normalization to targets_new
targets_normalized = [targets[i] * normalization_factors[i] for i in range(len(targets))]
# Recalculate RMS for normalized targets
rms_targets_normalized = [np.sqrt(np.mean(x ** 2, axis=0)) for x in targets_normalized]
# Plot the results
plt.figure()
plt.plot(rms_others, linewidth=5)
plt.plot(rms_targets, linewidth=1)
plt.plot(rms_targets_normalized, linewidth=2)
plt.legend(["Targets without AM", "Targets with AM (original)", "Targets with AM (normalized)"])

# check rms after level equalization
for tn, t, o in zip(targets_new, targets, others):
    tn.level = 50
    t.level = 50
    o.level = 50

# get all rms for stimuli
rms_targets = [np.sqrt(np.mean(x ** 2, axis=0)) for x in targets]
rms_others = [np.sqrt(np.mean(x ** 2, axis=0)) for x in others]
rms_targets_new = [np.sqrt(np.mean(x ** 2, axis=0)) for x in targets_new]

# Plot the results
plt.figure()
plt.plot(rms_others, linewidth=5)
plt.plot(rms_targets, linewidth=1)
plt.plot(rms_targets_new, linewidth=2)
plt.legend(["Targets without AM", "Targets with AM (original)", "Targets with AM (normalized)"])

# play sounds
[x.play() for x in targets_normalized]
[x.play() for x in targets]
[x.play() for x in targets_new]

