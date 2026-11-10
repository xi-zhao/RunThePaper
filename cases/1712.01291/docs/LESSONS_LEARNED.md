# Calculation checks / 复现札记

Fit kernel parameters on training prefixes. Predict the same time offsets one period apart with the fitted periodic kernel. Inspect the resulting periodicity separately from the risk on new held-out trajectories.

The original trajectories, training settings and tuning archive are missing. The package is bound to the frozen checkpoint and reruns the periodic GP; other forecasters retain protocol discrepancies.

[Derivation](DERIVATION.md)
