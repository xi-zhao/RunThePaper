"""Reclassify the pinned Ramsey frames and compare aggregate phase estimates."""
import argparse
import hashlib
import json
from pathlib import Path
from shutil import copyfile
import subprocess
import sys

import numpy as np

from metrics import phase
from run_reproduction import published_labels

RAMSEY_SHA256 = "497d77a0a242497988c269f300655ff588147f20f8bfee4b8e04522c8bdb308d"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--labels-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--method", choices=("threshold", "rf"), default="threshold")
    args = parser.parse_args()
    with args.archive.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != RAMSEY_SHA256:
            parser.error("Expected the pinned ramseydata.zip from the authors")
    reference = published_labels(args.labels_file)
    reference_phase = phase(reference.mean(axis=1))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "input").mkdir()
    (out / "results").mkdir()
    staged_archive = out / "input/ramseydata.zip"
    copyfile(args.archive, staged_archive)
    try:
        script = Path(__file__).with_name("classify_camera.py").resolve()
        subprocess.run([sys.executable, str(script), args.method], cwd=out, check=True)
    finally:
        staged_archive.unlink()
    with np.load(out / f"results/camera-{args.method}.npz", allow_pickle=False) as data:
        methods = ("threshold",) if args.method == "threshold" else ("rf_cv", "rf_archive_selector")
        summary = {}
        for name in methods:
            labels = data[name].reshape(reference.shape)
            estimated_phase = phase(labels.mean(axis=1))
            summary[name] = {
                "label_agreement": float(np.mean(labels == reference)),
                "max_phase_difference_rad": float(np.max(np.abs(estimated_phase - reference_phase))),
            }
    result = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    (out / "results/camera-summary.json").write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()
