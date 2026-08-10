# Method Trace

## MTH_CONTINUUM

- Source: Supplement MBM construction and Eqs. (M-model), (M-model-1)
- Input: alpha, complete reciprocal shell, k point
- Output: central eigenvalues/eigenvectors, velocity, gaps, bands
- Implementation: `src/tbg_topology/model.py::ContinuumModel`
- Check: Hermiticity, magic-velocity gate, cutoff-plus-one convergence
- Status: verified

## MTH_WILSON

- Source: Supplement Eq. (Wilson) and reciprocal embedding Eq. (embedding)
- Input: occupied-band frames on a closed reciprocal loop
- Output: continuous Wilson eigenphases
- Implementation: `ContinuumModel.wilson_spectrum`, `wilson_spectrum`
- Check: `k1 -> 2pi-k1` symmetry and winding class
- Status: verified

## MTH_NODE

- Source: Supplement discussion of Figs. 4-5
- Input: MBM central-band gap
- Output: node positions and vorticity signs
- Implementation: `reproduction.py::find_dirac_nodes`, `_dirac_vorticity`
- Check: gap residual and C3/torus multiplicity
- Status: verified

## MTH_WANNIER

- Source: Eqs. (proj-1), (proj-2), (psi-tilde), (HR)
- Input: lower four TB8-2V eigenstates and trial orbitals
- Output: nonsingular projected frame and real-space densities
- Implementation: `reproduction.py::projected_wannier`
- Check: paper's `det S(k)` interval
- Status: verified

## MTH_THEORY_PAPER_SCALE

- Scope: T001-T012, including every numerical series and subpanel already represented by the continuum/TB/Wannier solver
- Input: `config/theory_paper_scale.json`; printed physical parameters plus independently frozen production grids
- Entrypoint: `python scripts/run_theory_paper_scale.py --config config/theory_paper_scale.json --resume`
- Isolation: runtime inputs are only config and solver code; `raw/`, reference figures, source pixels, author code, and author arrays are absent from the run contract
- State rule: feature outputs are never overwritten; production data/checks live in the `paper_scale_theory` namespace and a resume is accepted only when config and output hashes all match
- Promotion boundary: a successful run is `paper_scale_reconstructed`; unpublished author cutoffs/grids and fresh review still prevent `paper_exact`
- Status: code ready; full production campaign not run

## MTH_DFT_GEOMETRY

- Source: paper TeX lines 1454-1471: commensurate-angle formula, `a0=2.456 Angstrom`, `d0=3.35 Angstrom`, AA starting bilayer, top-layer rotation about a carbon-hexagon centre, zero shift, and no relaxation
- Input: commensurate index `i`, `z/d0`, and 20 Angstrom vacuum
- Core model: `m=i+1`, `n=i`; one common periodic cell contains `4*(3*i^2+3*i+1)` carbon atoms
- Output: deterministic POSCAR coordinates for `i=6,10,16,23,27,30` and the five `i=10` distance jobs
- Implementation: `src/tbg_topology/dft_campaign.py::build_commensurate_structure`
- Check: exact atom count (up to 11164 at `i=30`), unique periodic sites, finite fractional coordinates, requested interlayer distance, and deck hashes
- Status: code ready; locally verified without VASP

## MTH_DFT_DECK

- Source: paper TeX lines 1454-1461: VASP/PAW, LDA, 300 eV, negligible SOC, unrelaxed structures; official VASP fixed-charge band workflow for the paper-omitted operational details
- Input: `config/dft_paper_scale.json`
- Method: Gamma-centred regular-mesh SCF followed by `ICHARG=11` non-self-consistent `M-Gamma-K-M` bands; the hexagonal K point is `(2/3,1/3)` in reciprocal fractional coordinates
- Explicit choices absent from the paper: VASP version, exact carbon PAW/POTCAR identity, SCF meshes, `EDIFF`, smearing, and band-path density
- Output: INCAR/POSCAR/KPOINTS decks plus a Slurm array script for 72 CPU and 2048 GiB per job
- Implementation: `prepare_campaign`, `render_incar`, `render_poscar`, `render_scf_kpoints`, `render_band_kpoints`
- Check: Carbon-LDA POTCAR must report one carbon dataset, `LEXCH=CA`, and `ZVAL=4`; its actual SHA-256 and the VASP executable SHA-256 are mandatory
- Status: code ready; licensed assets deliberately external

## MTH_DFT_EXECUTION

- Entrypoint: `python scripts/run_dft_campaign.py --config config/dft_paper_scale.json`
- State transition: `prepare -> preflight -> run-job (SCF -> bands) -> analyze`
- Resume rule: a stage is skipped only when OUTCAR contains VASP's completion marker; incomplete stages retain checkpoints and remain retryable
- Attestation: one config hash, every input-deck hash, VASP executable hash/version, POTCAR metadata/hash, machine allocation, per-job OUTCAR/EIGENVAL hashes, and all 11 job receipts must agree before analysis
- External blocker: licensed VASP, a licensed Carbon-LDA POTCAR, explicit acknowledgement that the paper omitted the PAW identity, and paper-scale scheduler quota
- Status: executable but not externally run in this repository

## MTH_DFT_ANALYSIS

- D001: twelve Gamma eigenlevels around neutrality for each angle job, reported relative to that job's Fermi energy; distance jobs cannot enter this aggregate
- D002/D012: neutrality gap at the true Moire K point for the angle and distance sweeps
- D003-D011: twelve bands around neutrality along `M-Gamma-K-M`
- Scientific gates: all six Gamma indices present; reported 4-2-2-4 `i=6` multiplets within tolerance; lower/upper isolation-gap minima at `i=16`/`i=30`; K-gap local minimum at `i=10` followed by growth; exact distance list `1.00,0.90,0.86,0.83,0.80`; distance K gap nondecreasing under compression
- Implementation: `analyze_campaign`, `evaluate_science`
- Status: code ready; gates cannot pass until attested VASP outputs exist

## MTH_RENDER

- Source: case render contract
- Input: frozen generated arrays and, only downstream, source panels
- Output: figures, comparisons, pixel metrics
- Implementation: `scripts/render_figures.py`, `prepare_reference_panels.py`, `build_comparisons.py`
- Check: all numerical hashes unchanged after rendering
- Status: verified for T001-T012; D001-D012 remain pending the external DFT run

The DFT runtime does not read `raw/`, `references/`, author code, author arrays, or figure pixels. Paper source files were used only to transcribe the method and the five printed Supplement Fig. 12(a) labels into the frozen configuration.
