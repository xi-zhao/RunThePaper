"""Save a package-validation receipt bound to the exact checked Git commit."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(root, expected_sha, receipt):
    sha = subprocess.check_output(["git", "--no-replace-objects", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    errors = []
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha) or sha != expected_sha:
        errors.append("HEAD differs from the requested exact publication SHA")
    if subprocess.run(["git", "--no-replace-objects", "diff", "--quiet", "HEAD", "--"], cwd=root).returncode:
        errors.append("tracked working files differ from the publication commit")
    tracked = {}
    for item in subprocess.check_output(["git", "--no-replace-objects", "ls-tree", "-rz", "HEAD"], cwd=root).split(b"\0"):
        if not item: continue
        info,name=item.split(b"\t",1)
        mode,kind,oid=info.decode().split()
        tracked[name.decode()] = (mode,kind,oid)
    algorithm=subprocess.check_output(["git", "--no-replace-objects","rev-parse","--show-object-format"],cwd=root,text=True).strip()
    for name,(mode,kind,oid) in tracked.items():
        path=root/name
        if name.startswith('cases/') and (path.suffix=='.pyc' or path.name=='.DS_Store'):
            errors.append('transient file must not be published: '+name)
        if kind!='blob' or path.is_symlink() or not path.is_file():
            errors.append('publication input is not a regular committed blob: '+name)
            continue
        data=path.read_bytes()
        actual=hashlib.new(algorithm,b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual!=oid or bool(path.stat().st_mode & 0o111)!=(mode=='100755'):
            errors.append('publication bytes or mode differ from HEAD: '+name)
    for folder in ("scripts", "cases", "tests"):
        for path in (root / folder).rglob("*"):
            if not path.is_file() or path.suffix == ".pyc" or path.name == ".DS_Store":
                continue
            if path.relative_to(root).as_posix() not in tracked or path.is_symlink():
                errors.append("validation input is not a regular committed file: "
                              + path.relative_to(root).as_posix())
    for path in root.glob('*.md'):
        if path.name not in tracked or path.is_symlink():
            errors.append('root document is not a regular committed file: '+path.name)
    validation_env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1")
    result = subprocess.run([sys.executable, "scripts/validate_public_cases.py"],
                            cwd=root, env=validation_env, capture_output=True, text=True)
    log = result.stdout + result.stderr
    if result.returncode:
        errors.append("public package validator failed")
    rendered = subprocess.run([sys.executable, "scripts/render_case_catalog.py", "--check"],
                              cwd=root, env=validation_env, capture_output=True, text=True)
    log += rendered.stdout + rendered.stderr
    if rendered.returncode:
        errors.append("generated navigation differs from the committed catalog")
    receipt = Path(receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    log_path = receipt.with_suffix(".log")
    log_path.write_text(log, encoding="utf-8")
    payload = {"format": "runthepaper.publication-validation.v1",
               "publication_sha": sha, "expected_sha": expected_sha,
               "passed": not errors, "errors": errors,
               "validator_exit_code": result.returncode,
               "navigation_exit_code": rendered.returncode,
               "validator_log_sha256": hashlib.sha256(log.encode()).hexdigest(),
               "scientific_acceptance": "not_assessed_by_package_validator",
               "private_source_access": "not_checked_by_public_ci",
               "github_run_id": os.environ.get("GITHUB_RUN_ID"),
               "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT")}
    receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(log, end="")
    print(json.dumps(payload, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    sys.exit(verify(ROOT, args.expected_sha, args.receipt))
