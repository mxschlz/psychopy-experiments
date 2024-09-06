import os
import slab
import numpy as np
import matplotlib.pyplot as plt
from utils.signal_processing import modulate_amplitude
# import matplotlib
# matplotlib.use("Qt5Agg")
plt.ion()


# load sounds
singletons = [slab.Sound.read(f"stimuli/distractors_high/{x}")
              for x in os.listdir(f"stimuli/distractors_high")]
targets = [slab.Sound.read(f"stimuli/targets/{x}") for x in os.listdir(f"stimuli/targets")]
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
plt.plot(rms_others, alpha=0.7)
plt.plot(rms_targets, alpha=0.7)
plt.plot(rms_targets_normalized, alpha=0.7)
plt.legend(["Targets without AM", "Targets with AM (original)", "Targets with AM (normalized)"])

[x.play() for x in targets_normalized]
[x.play() for x in targets]
[x.play() for x in targets_new]


