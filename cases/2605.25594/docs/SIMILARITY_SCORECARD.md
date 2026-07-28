# Similarity Scorecard

## Overall

- Overall score: `67.49/100`
- Level: `numerical_feature_reproduction`
- Check status: `partial`

The score includes the completed A100 campaign at `L=24,28,31` with 605
disorder realizations, plus the smaller mechanism and phenomenological checks.
It remains a paper-scale subset reproduction: all nine targets are explicitly
exploratory, and none is promoted to a final reproduction.

## Figure-Level Scores

| Paper item | Score | Parameter match | Main boundary |
| --- | ---: | --- | --- |
| Fig. 1 — susceptibility versus disorder | 79 | paper subset | A100 sizes resolve the delocalized-side peak, but do not complete the paper's full size ladder. |
| Fig. 2 — weak-crossover scaling | 62 | reduced scale | The asymptotic `41/sqrt(V)` fit is not closed. |
| Fig. 3 — spectral function | 65 | paper subset | The mechanism is reproduced, but the large-volume exponent and width remain incomplete. |
| Fig. 8 — typical/average separation | 72 | paper subset | The localized-regime split is visible without the paper's full large-size `mu` sweeps. |
| Fig. A1 — adjacent-gap ratio | 79 | paper subset | GOE-to-Poisson endpoints and the transition window agree at the completed A100 sizes. |
| Fig. A3 — large-volume spectral scaling | 41 | paper subset | Insufficient compute for the paper's large-volume scaling target. |
| Fig. 9 — typical susceptibility | 70 | paper subset | Feature-level agreement; the full size ladder remains incomplete. |
| Fig. 10 — perturbative trend | 60 | reduced scale | The implementation validates the strong-disorder trend, not an absolute normalization. |
| Fig. 11 — phenomenological envelope | 65 | paper subset | The exponent is self-consistent, but exact curve tuning needs unpublished inputs. |

## Reproduction Boundary

The paper's central claims are scale-sensitive:

- The completed `L=24,28,31` campaign supports the fidelity-susceptibility and
  level-statistics trends, but the paper's `L=32-38` ladder is not complete.
- `L=32` hit a 32-bit eigensolver-workspace failure and `L=38` exceeds the
  practical single-A100 dense-eigensolver path.
- The `T` and randomized-site `n` operator panels remain outside the completed
  subset.
- The printed slow-mode continuum exponent is internally inconsistent; the
  reproduction publishes the corrected derivation as `reconstructed`.

For these reasons, the evidence is useful and paper-scale, but every target
keeps the `exploratory` stage label.

## Machine-Readable Record

See `outputs/checks/similarity_scorecard.json`.
