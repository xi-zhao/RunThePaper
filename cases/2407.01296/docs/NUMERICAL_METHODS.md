# Numerical Methods

## Shared numerical core

Geometries are explicit integer site sets. Laurent monomials are expanded to displacement/amplitude pairs, and OBC matrices retain a hopping only when both endpoints are inside the site set. This separates physical coefficients from square, diamond, cut-interval, and chain geometries.

The case uses dense or sparse eigensolvers according to the required observable, formula-derived spectral potentials, finite differences for spectral density, integer phase windings, and paired left/right eigenvectors for biorthogonal perturbation theory. Every state density is normalized and every selected eigenpair carries a residual.

## Unified T004–T009 campaign

`scripts/run_supplemental_campaign.py` reads one immutable JSON profile and writes one data artifact per target, a science record, per-target hash-bound checkpoints, and a final manifest. `--resume` accepts a checkpoint only if configuration SHA, implementation SHA, output existence and output SHA all match.

The smoke profile is an executable correctness proof. The paper profile expands the same kernels to:

- Fig. 2(d): four declared colored regions plus a 101×101 global plane over size sequences;
- S2: N=5625 separable spectrum and formula/Amoeba density grids;
- S4: printed chain sizes and dense momentum sampling;
- S5: N≈6400 square/rhombus spectra, states, scaling and Eq. (10) densities;
- S6: 361 transverse slices and 4096 points per loop;
- S7: six sizes, disorder sweep and multiple realizations.

## Isolation and rendering

The run contract blocks raw sources, references, original figures, author arrays, network and subprocesses. The v5 run had 0 forbidden accesses. Rendering is a second process that hashes every input before and after drawing and may change only layout properties; it cannot modify arrays, physics parameters or curve coordinates.

## Commands

```bash
PYTHONPATH=case/2407.01296/workspace python -m pytest -q case/2407.01296/tests
PYTHONPATH=PRAgent-workflow python PRAgent-workflow/scripts/run_isolated_numerics.py case/2407.01296 --contract case/2407.01296/run_contract.supplemental_smoke.json
cd case/2407.01296/workspace
python scripts/run_supplemental_campaign.py --config config/supplemental_paper_scale.json --profile paper --output-root outputs/data/supplemental_paper_v1 --resume
python scripts/render_supplemental_campaign.py --input-root outputs/data/supplemental_paper_v1 --output-root outputs/figures/supplemental_paper_v1
```
