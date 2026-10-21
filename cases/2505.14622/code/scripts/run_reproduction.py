"""Rerun the paper model and a distinct numerical formulation in a fresh directory."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New directory; existing paths are refused.')
    args = parser.parse_args()
    code = Path(__file__).resolve().parents[1]
    case = code.parent
    out = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix='prl-rerun-'))
    if args.output:
        out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(code/'model', out/'calculation')
    checks = out/'calculation/checks'
    checks.mkdir(exist_ok=True)
    shutil.copyfile(case/'outputs/checks/numerical-checks.json', checks/'results.json')
    env = dict(os.environ, MPLBACKEND='Agg', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    subprocess.run([sys.executable, str(out/'calculation/generate.py')], cwd=out, env=env, check=True)
    manifest = {}
    for p in sorted((out/'calculation').rglob('*')):
        if p.is_file() and p.suffix != '.pyc':
            manifest[p.relative_to(out).as_posix()] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    (checks/'audit-input-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    subprocess.run([sys.executable, str(checks/'audit.py')], cwd=out, env=env, check=True)
    audit_path = next(checks.glob('audit-*-results.json'))
    audit = json.loads(audit_path.read_text())
    failures = []
    def walk(value, path=''):
        if isinstance(value, dict):
            for k, v in value.items():
                if k in {'within_tolerance', 'class_matches_summary', 'C_shift_within_printed_rounding'} and v is False:
                    failures.append(path+'/'+k)
                walk(v, path+'/'+k)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, path+'/'+str(i))
    walk(audit)
    assert all(audit['input_integrity'].values()), audit['input_integrity']
    assert not failures, failures
    with np.load(out/'calculation/results/generation.npz') as new, np.load(case/'outputs/data/generation.npz') as frozen:
        assert set(new.files) == set(frozen.files)
        errors = {}
        for key in new.files:
            assert new[key].shape == frozen[key].shape, key
            if new[key].dtype.kind == 'b' or frozen[key].dtype.kind == 'b':
                errors[key] = float(np.count_nonzero(new[key] != frozen[key]))
                assert np.array_equal(new[key], frozen[key]), key
            else:
                errors[key] = float(np.max(np.abs(new[key]-frozen[key])))
                assert np.allclose(new[key], frozen[key], atol=1e-10, rtol=1e-10), (key, errors[key])
    subprocess.run([sys.executable, str(out/'calculation/render.py')], cwd=out, env=env, check=True)
    if (code/'alignment').is_dir():
        shutil.copytree(code/'alignment', out/'alignment')
        subprocess.run([sys.executable, str(out/'alignment/compute.py')], cwd=out/'alignment', env=env, check=True)
    summary = {'paper_id': case.name, 'array_count': len(errors), 'max_abs_array_difference': max(errors.values()),
               'audit': audit_path.relative_to(out).as_posix(), 'checks_passed': True,
               'scope': 'Fresh model generation and distinct numerical checks; reference-curve extraction is not rerun.',
               'figure_annotations': 'Frozen numerical-check annotations are retained for the unchanged published parameters.'}
    (out/'rerun-checks.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({'output': str(out), **summary}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
