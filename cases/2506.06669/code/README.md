# Runnable code for 2506.06669

Run commands from the repository root unless a command below changes directory.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd cases/2506.06669/code
python scripts/verify_public_artifacts.py
```

## Independent numerical rerun

This command recomputes the scientific numerical arrays from the public equation-based implementation. It does not read a paper image, digitized source curve, or author numerical code; runtime varies from seconds to CPU minutes.

```bash
cd cases/2506.06669/code
python scripts/run_reproduction.py --config config/paper_reconstruction.json
```

Generated data files are written to `../outputs/data/`, figures to `../outputs/figures/`, and machine-readable checks to `../outputs/checks/`.

Boundary: Frozen non-final target states: T001=figure_rendered, T002=figure_rendered, T003=figure_rendered, T004=figure_rendered, T005=figure_rendered, T006=figure_rendered, T007=figure_rendered, T008=figure_rendered, T009=figure_rendered, T010=figure_rendered. No source-image comparison panel or digitized source curve is published in this projection.
