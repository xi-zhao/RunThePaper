"""Run the documented independent calculations in a fresh output directory."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import mkdtemp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="A new result directory")
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    code = scripts.parent
    steps = json.loads((code / "run-steps.json").read_text(encoding="utf-8"))
    if args.output is None:
        output = Path(mkdtemp(prefix="runthepaper-rerun-"))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    if (code / "config").is_dir():
        shutil.copytree(code / "config", output / "config")
    (output / "results").mkdir()
    for script, *arguments in steps:
        subprocess.run([sys.executable, "-B", str(scripts / script), *arguments], cwd=output, check=True)
    print(f"Results saved to {output / 'results'}")


if __name__ == "__main__":
    main()
