"""Plot only generated smooth-protocol energies; no paper coordinates are read."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

a = np.load('calculation/results/generation.npz')
fig, ax = plt.subplots(figsize=(8, 4))
for ms in [25, 15, 10, 6, 2]:
    ax.plot(a['s'], a[f'{ms}ms_poly_energy'], label=f'{ms} ms')
ax.set(xlabel='t / final time', ylabel='Energy / initial ground energy',
       title='Independent smooth shortcut protocols')
ax.legend()
fig.tight_layout()
dest = Path('figures/overview.png')
dest.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(dest, dpi=150)
