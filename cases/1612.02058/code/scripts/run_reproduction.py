"""Run the published scientific implementation in a new output directory."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New directory; an existing path is refused.')
    parser.add_argument('--experiment', default='generate.py', help='Relative Python entrypoint in code/model.')
    args = parser.parse_args()
    code = Path(__file__).resolve().parents[1]
    entry = Path(args.experiment)
    if entry.is_absolute() or '..' in entry.parts or entry.suffix != '.py':
        parser.error('experiment must be a relative Python file in code/model')
    if not (code/'model'/entry).is_file():
        parser.error('entrypoint is not included in this public package')
    out = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix='paper-rerun-'))
    if args.output:
        out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(code/'model', out/'calculation')
    (out/'calculation/results').mkdir(exist_ok=True)
    env = dict(os.environ, MPLBACKEND='Agg', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               PYTHONPATH=str(out/'calculation'))
    subprocess.run([sys.executable, str(out/'calculation'/entry)], cwd=out, env=env, check=True)
    summary = {'entrypoint': entry.as_posix(), 'process': 'finished',
               'boundary': 'Fresh scientific calculation and its embedded checks. This is not whole-paper acceptance.'}
    if entry.as_posix() == 'generate.py':
        import numpy as np
        case = code.parent
        errors = {}
        with np.load(out/'calculation/results/generation.npz') as fresh, np.load(case/'outputs/data/generation.npz') as frozen:
            if set(fresh.files) != set(frozen.files):
                raise AssertionError('output array inventory changed')
            for key in fresh.files:
                a, b = fresh[key], frozen[key]
                if a.shape != b.shape:
                    raise AssertionError((key, a.shape, b.shape))
                if a.dtype.kind in 'bu' and b.dtype.kind in 'bu':
                    equal = np.array_equal(a, b)
                    errors[key] = float(np.count_nonzero(a != b))
                else:
                    equal = np.allclose(a, b, atol=1e-8, rtol=1e-8, equal_nan=True)
                    errors[key] = float(np.nanmax(np.abs(a-b))) if a.size else 0.
                if not equal:
                    raise AssertionError((key, errors[key]))
        summary.update(array_count=len(errors), max_abs_array_difference=max(errors.values(), default=0.),
                       frozen_array_comparison='passed at atol=rtol=1e-8', array_errors=errors)
    (out/'rerun-checks.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({'output': str(out), **{k:v for k,v in summary.items() if k!='array_errors'}}, indent=2))


if __name__ == '__main__':
    main()
