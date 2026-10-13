"""Reanalyse owned trajectories; no new trajectories and no author data.

The frozen archive includes unmodified simulation outputs and their generation
identities/checksums. This run records derived arithmetic for the H2 objects.
"""
import hashlib
import io
import json
import zipfile
from pathlib import Path
import numpy as np


def main():
    with zipfile.ZipFile('inputs/h2-binning-v1.zip') as z:
        lineage=json.loads(z.read('lineage.json'))
        for item in lineage['files']:
            assert hashlib.sha256(z.read(item['archive_path'])).hexdigest()==item['sha256']
        meta=json.loads(z.read('dynamics.json'));data=np.load(io.BytesIO(z.read('dynamics.npz')))
        gs=np.load(io.BytesIO(z.read('coherent-gs.npz')))
        initial={m['statistics']+'_'+s['id']:s for m in meta['config']['models'] for s in m['initial_states']}
        rows=[]
        for row in meta['results']:
            key=row['id'];state=initial[key]
            if 'occupations' in state:
                q0=sum((i+1)*n for i,n in enumerate(state['occupations']))
                q=q0-np.array([d['jumps'] for d in row['diagnostics']])
                photon=data[key+'_photon'];X=data[key+'_X'];assert np.all(photon>=0)
                bins=q-np.ceil(photon).astype(int)
                assert np.max(abs(X+photon-q))<1e-9
                rows.append(dict(id=key,bins=bins.tolist(),photon=photon.tolist(),Q=q.tolist(),X=X.tolist(),definition='Q-ceil(photon)'))
            else:
                X=gs[key+'_X'];rows.append(dict(id=key,bins=np.floor(X).astype(int).tolist(),X=X.tolist(),definition='floor(coherent mean X)'))
    out=Path('outputs/h2-bin-derivation-v1/results.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(dict(rows=rows,lineage=lineage,
        interpretation='Derived bin arithmetic on exactly the prior 5000 Fock and 200 coherent GS trajectories; no added sampling or source reference input.'),indent=2)+'\n')
    print(json.dumps({'Fock_trajectories':sum(len(r['bins']) for r in rows if 'Q' in r),'coherent_GS_trajectories':sum(len(r['bins']) for r in rows if 'Q' not in r)}))


if __name__=='__main__':main()
