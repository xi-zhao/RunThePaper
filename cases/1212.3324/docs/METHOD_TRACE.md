# Method trace

| Target | Source object | Independent implementation | Main falsification/check |
| --- | --- | --- | --- |
| T001 | Fig. 2(c) | exact five-step open-strip Floquet product | bulk ideal-point operator equals identity |
| T002 | Fig. 3(a) | strip unitary eigenspectrum at $J/\pi=0.5$ | no gap-spanning edge-localized branch; $(W_0,W_\pi)=(0,0)$ |
| T003 | Fig. 3(b) | strip unitary eigenspectrum at $J/\pi=1.5$ | pi-gap branch and independent $C=1$, $(0,1)$ |
| T004 | Fig. 3(c) | strip unitary eigenspectrum at $J/\pi=2.5$ | edge branches in both gaps and independent $C=0$, $(1,1)$ |
| T005 | Fig. 3(d) | Brillouin-zone bulk-gap scan | both delta_AB conventions retained; no source-pixel fit |
| T006 | Fig. 6(a) | analytic two-band bulk eigensurfaces | resonance contour sampled and static $|C|=1$ |
| T007 | Fig. 6(b) | hand-derived plus inverse-Bloch-Fourier open-y Hamiltonians | matrix parity, Hermiticity and boundary localization |
| T008 | Fig. 6(c) | repeated-zone block Hamiltonian built from independently checked strip blocks | matrix parity, Hermiticity plus separate real-time Floquet Chern |
| T009 | text claims | full-evolution winding and Fukui Chern | $C=W_\pi-W_0$ and time-grid convergence |

The scientific runner can read only the declared config and implementation
files.  `raw/` and `references/` are forbidden roots.  Original figures become
available only after the numerical output manifest has frozen every data hash,
and then only to the separate RenderContract path.
