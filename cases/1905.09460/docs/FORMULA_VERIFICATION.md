# Formula Verification

All eight numerical formula cards pass the source-and-derivation gate. The
machine-readable result is `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Verification |
| --- | --- | --- | --- |
| EQ001 | non-Hermitian AAH Hamiltonian | open | Hermitian limit, PT identity, and boundary contracts tested |
| EQ002 | Fourier-dual Hatano-Nelson model | open | rational approximant spectra agree to numerical precision |
| EQ003 | common threshold `h_c=log(2J/V)` | open | symbolic derivation and `J=V=1` limiting value checked |
| EQ004 | determinant winding | open | stable determinant-circle derivation and phase unwrapping checked |
| EQ005 | IPR and edge localization | open | normalization and limiting-state tests pass |
| EQ006 | laser field and saturated gain | open/reconstructed | printed equations verified; stationary neutral-growth reduction disclosed |
| EQ007 | laser spectral bandwidth | open/reconstructed | gain-centred RMS estimator is explicit and tested |
| EQ008 | exact/first-order etalon transmission | open | Fresnel reflectance, periodicity, and approximation error checked |

## Source issues resolved

- Main text after Eq. (4) prints `V_-n=-V_n*`; direct cosine expansion gives
  `V_-n=V_n*`. The implementation uses the algebraically correct PT identity.
- Supplement S.1 calls the `h>h_c` regime “unbroken PT” once; the spectra and
  the rest of the paper show that it is the broken phase.
- The laser paragraph prints `alpha=(sqrt(5)-1)/4`, while the Fig. 3 caption,
  Supplement S.4, and `1.3844/2.24` all give `(sqrt(5)-1)/2`. The mutually
  consistent value is used.
- Supplement Eq. (S-31) gives `theta=phi+pi/2`. With the natural `phi=0`
  convention, the laser run uses `theta=pi/2`, centring the localized low-depth
  mode at `n=0`.

## Remaining method uncertainty

The paper does not report the laser mode cutoff, random seed, integration time,
dimensionless gain-relaxation control, or bandwidth estimator. It also does not
define the edge-state counting rule. These affect evidence level, not formula
provenance: both targets remain explicitly reconstructed rather than being
promoted to exact transient reproductions.
