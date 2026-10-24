"""Managed generation v2 (fixed-v2 conditions only; no reference ordinates).

Dynamics: hard-wall L=600, N=30 (box Lin=150, superlattice A=8, period 4).
Ensembles: GGE with (a) hard-wall standing-wave occupations and (b) periodic
plane-wave occupations, the latter being the source's stated convention for
theoretical predictions ("For our theoretical predictions we use a periodic
lattice"). Grand-canonical ensemble fitted to N and E.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMBA_NUM_THREADS'] = '4'; os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, 'code')
from hcb import free_modes, initial_box, initial_super, occupations, thermal, pure_rho_direct, gaussian_real_rho, momentum

cfg = json.loads(Path('code/config.json').read_text()); L, N = cfg['L'], cfg['N']
e, U = free_modes(L); x = np.arange(1, L + 1); start = time.monotonic(); out = {'k': np.arange(-L // 2, L // 2)}


def plane_wave_gge(P, shift=0.5, cutoff=240):
    q = 2 * np.pi * (np.arange(L) + shift) / L
    W = np.exp(1j * np.outer(x, q)) / np.sqrt(L)
    n = np.sum(abs(W.conj().T @ P) ** 2, axis=1)
    C = ((W * n) @ W.conj().T).real
    return momentum(gaussian_real_rho(C, cutoff))


extra = {'box': [4000, 5000, 7500, 10000, 20000], 'super': list(np.arange(0.5, 50, 0.5)[::2])}
for name in ['box', 'super']:
    P = initial_box(L, N, cfg['Lin']) if name == 'box' else initial_super(L, N, cfg['A'])
    n, Q = occupations(U, P)
    out[name + '_gge_obc'] = momentum(gaussian_real_rho((U * n) @ U.T, 240))
    for shift in (0.5, 0.0):
        out[f'{name}_gge_pw{shift}'] = plane_wave_gge(P, shift)
    out[name + '_gge_pw_cutoff160'] = plane_wave_gge(P, 0.5, 160)
    nt, z = thermal(e, n)
    out[name + '_thermal'] = momentum(gaussian_real_rho((U * nt) @ U.T, 160))
    times = sorted(set(map(float, cfg[name + '_times'])) | set(map(float, extra[name])))
    fs = []
    for i, t in enumerate(times):
        Pt = U @ (np.exp(-1j * e * t)[:, None] * Q)
        fs.append(momentum(pure_rho_direct(Pt.astype(complex))))
        if i % 25 == 0:
            print(name, i, len(times), t, fs[-1][L // 2], round(time.monotonic() - start, 1), flush=True)
    out[name + '_times'] = np.array(times); out[name + '_f'] = np.array(fs)
sweep = {}
for Lin in cfg['sweep_Lin']:
    P = initial_box(L, N, Lin); n, Q = occupations(U, P)
    f = momentum(pure_rho_direct((U @ (np.exp(-1j * e * 3000)[:, None] * Q)).astype(complex)))
    g = momentum(pure_rho_direct(P.astype(complex))) if Lin == L else momentum(gaussian_real_rho((U * n) @ U.T, 360))
    out[f'sweep_{Lin}_late'] = f; out[f'sweep_{Lin}_gge_obc'] = g
    sweep[str(Lin)] = {'max_abs': float(abs(f - g).max()), 'L1_over_N': float(abs(f - g).sum() / N), 'f0': float(f[L // 2])}
    print('sweep', Lin, sweep[str(Lin)], flush=True)
Path('results').mkdir(exist_ok=True)
np.savez_compressed('results/generation_v2.npz', **out)
Path('results/generation_v2.json').write_text(json.dumps({'sweep': sweep, 'wall_seconds': time.monotonic() - start}, indent=2))
print('finished', time.monotonic() - start, flush=True)
