"""Download and verify the public benchmark archive used as raw input."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = PACKAGE_ROOT.parent
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from benchmark_release import (  # noqa: E402
    ARCHIVE_FILENAME,
    ARCHIVE_URL,
    BenchmarkReleaseError,
    validate_archive,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download the authors' CC-BY-4.0 benchmark release. The independent "
            "optimizer later opens only its 122 raw circuit/observable payloads."
        )
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=CASE_ROOT / "inputs" / ARCHIVE_FILENAME,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing archive only after the replacement validates.",
    )
    return parser.parse_args()


def download(destination: Path, *, force: bool) -> dict[str, object]:
    destination = destination.resolve()
    if destination.is_file() and not force:
        try:
            return {"downloaded": False, **validate_archive(destination)}
        except BenchmarkReleaseError as exc:
            raise BenchmarkReleaseError(
                f"Existing archive is invalid; pass --force to replace it: {exc}"
            ) from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.part")
    temporary.unlink(missing_ok=True)
    try:
        with urllib.request.urlopen(ARCHIVE_URL, timeout=60) as response:
            with temporary.open("wb") as handle:
                while block := response.read(1024 * 1024):
                    handle.write(block)
        validation = validate_archive(temporary)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    validation["path"] = str(destination)
    return {"downloaded": True, **validation}


def main() -> int:
    args = parse_args()
    print(json.dumps(download(args.destination, force=args.force), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
