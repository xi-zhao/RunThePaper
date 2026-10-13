"""One frozen memory curve point per observed process, for failure isolation.

The original circuit, noise, BP+LSD_CS order 2, and samples are unchanged.
This wrapper fixes ambiguous output labels and validates the window domain.
"""
import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path
import simulate_memory_v1 as memory


def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,required=True);a=p.parse_args()
    cfg=json.loads(Path('config/memory-bplsd-v1.json').read_text())
    job=cfg['jobs'][a.index]
    if job['rounds']+1<3:raise ValueError('W=3 requires at least three detector blocks including terminal closure')
    out=Path(f'outputs/memory-points-v2/point{a.index:02d}')
    cfg=dict(cfg,jobs=[job],output_dir=str(out))
    with tempfile.TemporaryDirectory(prefix='memory-point-') as tmp:
        config=Path(tmp)/'config.json';config.write_text(json.dumps(cfg))
        sys.argv=['simulate_memory_v1.py','--config',str(config)]
        memory.main()
    r=json.loads((out/'results.json').read_text());row=r['rows'][0]
    row['decoder']['solver_seconds']=row['decoder'].pop('milp_seconds')
    r['source_config_job_index']=a.index
    r['interpretation']='Declared SD6 circuit and W3/S1 BP+LSD_CS order-2 decoder; syndrome satisfaction is checked, MLE optimality is not claimed. Ideal boundaries and matching-basis logical parity definition remain explicit.'
    (out/'results.json').write_text(json.dumps(r,indent=2)+'\n')
    with zipfile.ZipFile(out/'samples-circuit.zip','w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(out.iterdir()):
            if file.suffix in ('.npz','.stim') or file.name.endswith('-schedule.json'):z.write(file,file.name)


if __name__=='__main__':main()
