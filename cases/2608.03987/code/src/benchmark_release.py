"""Identity and integrity contract for the public RealifyTN benchmark release.

The release contains several kinds of artifacts.  The independent optimizer
consumes only the raw circuit payloads selected in
``run_independent_reimplementation.py``; this module merely pins and validates
the immutable ZIP that carries them.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Any


ARCHIVE_FILENAME = "NPUBenchmarkData-release.zip"
ARCHIVE_URL = (
    "https://zenodo.org/api/records/21791682/files/"
    "NPUBenchmarkData-release.zip/content"
)
ARCHIVE_RECORD_URL = "https://doi.org/10.5281/zenodo.21791682"
ARCHIVE_SHA256 = "719bd15ebb4fa4c54a3e8c433577a824956bff37ab480ecc84387649d5aa8b9e"
ARCHIVE_MD5 = "ab3a96974ee0163f524708f30120cb97"
RELEASE_PREFIX = "NPUBenchmarkData-release/"

RANDOM_PANEL_ORDER = (
    "test",
    "rectangular_4x4_1-16-1_0",
    "rochester_53_8_0_pABC",
    "rectangular_6x6_1-32-1_0",
    "bristlecone_48_1-16-1_0",
    "rectangular_6x6_1-24-1_0",
    "rectangular_6x6_1-16-1_0",
    "bristlecone_70_1-16-1_0",
    "sycamore_53_10_0",
    "rochester_53_12_0_pABC",
    "bristlecone_70_1-24-1_0",
    "rectangular_8x8_1-24-1_0",
)


class BenchmarkReleaseError(RuntimeError):
    """Raised when the immutable benchmark release violates its contract."""


def file_digest(path: Path, algorithm: str) -> str:
    hasher = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def validate_archive(archive_path: Path) -> dict[str, Any]:
    """Validate release identity and ZIP integrity without consuming results."""

    archive_path = archive_path.resolve()
    if not archive_path.is_file():
        raise BenchmarkReleaseError(f"Benchmark archive is missing: {archive_path}")
    sha256 = file_digest(archive_path, "sha256")
    md5 = file_digest(archive_path, "md5")
    if sha256 != ARCHIVE_SHA256 or md5 != ARCHIVE_MD5:
        raise BenchmarkReleaseError(
            "Benchmark archive checksum mismatch: "
            f"sha256={sha256}, md5={md5}"
        )
    with zipfile.ZipFile(archive_path) as release:
        bad_member = release.testzip()
        member_count = len(release.infolist())
    if bad_member is not None:
        raise BenchmarkReleaseError(f"Corrupt ZIP member: {bad_member}")
    return {
        "status": "passed",
        "path": str(archive_path),
        "bytes": archive_path.stat().st_size,
        "sha256": sha256,
        "md5": md5,
        "zip_members": member_count,
        "zip_integrity": "passed",
        "record_url": ARCHIVE_RECORD_URL,
    }
