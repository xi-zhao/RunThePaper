"""Regenerate the pulse-propagation, benchmarking and autocorrelation results."""
import argparse
from pathlib import Path
import subprocess
import sys
from tempfile import mkdtemp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New output directory")
    args = parser.parse_args()
    if args.output is None:
        output = Path(mkdtemp(prefix="qc27-rerun-"))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    (output / "results").mkdir()
    scripts = Path(__file__).resolve().parent
    for name in ("generate.py", "autocorrelation.py"):
        subprocess.run([sys.executable, str(scripts / name)], cwd=output, check=True)
    print(f"Wrote {output / 'results'}")


if __name__ == "__main__":
    main()
