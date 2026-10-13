"""Re-decode only the pilot's unresolved Bell syndromes; no new sampling."""
import io
import hashlib
import json
import time
import zipfile
from pathlib import Path
import numpy as np
from generate_pauli_probe_v1 import rate_summary
from simulate_sd6_factory_v2 import factory, Decoder
from structured_schedule import structured_tri


def main():
    out=Path('outputs/pauli-probe-refined-v1');out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile('inputs/pauli-pilot-v1.zip') as z:
        lineage=json.loads(z.read('lineage.json'))
        for p,h in lineage['sha256'].items():assert hashlib.sha256(z.read(p)).hexdigest()==h
        data=json.loads(z.read('results.json'));saved=zipfile.ZipFile(io.BytesIO(z.read('samples-circuits.zip')))
        models=json.loads(Path('config/models.json').read_text())['pairs']
        arrays={};changes=[];start=time.monotonic()
        for row in data['rows']:
            tag=f"n{row['n4']}_p{row['p']:.8g}_s{row['seed']}"
            blob=np.load(io.BytesIO(saved.read(tag+'.npz')))
            a={k:blob[k].copy() for k in blob.files};before=a['bell_errors'].copy();known=a['bell_known'].copy()
            model=next(m for m in models if m['quad'][0]==row['n4'])
            c,dem,meta=factory(model,row['p'],row['pccz'],probe='bell',tri_override=structured_tri(model,(0,2,1,3)))
            assert str(c)==saved.read(tag+'-bell.stim').decode()
            decoder=Decoder(dem,120);accepted_obs=a['obs'][a['accept']];accepted_det=a['det'][a['accept']]
            remaining=[]
            for i in np.flatnonzero(~known):
                try:
                    pred=decoder.predict(accepted_det[i].astype(np.uint8))
                    a['bell_errors'][i]=accepted_obs[i]^pred;a['bell_known'][i]=True
                    changes.append(dict(n4=row['n4'],accepted_index=int(i),errors=a['bell_errors'][i].tolist()))
                except RuntimeError as exc:remaining.append(dict(index=int(i),reason=str(exc)))
            assert np.array_equal(before[known],a['bell_errors'][known])
            be,bk=a['bell_errors'],a['bell_known'];pe,pk=a['phase_errors'],a['phase_known'];both=bk&pk
            row.update(bell_z=rate_summary(be[:,:3],bk),bell_x=rate_summary(be[:,3:],bk),bell_any=rate_summary(be[:,:3]|be[:,3:],bk),
                       unknown_bell_patterns=remaining,paired_known=int(both.sum()),
                       phase_success_bell_failure=int(np.sum(~pe[both].any(axis=1)&be[both].any(axis=1))),
                       phase_failure_bell_success=int(np.sum(pe[both].any(axis=1)&~be[both].any(axis=1))))
            stream=io.BytesIO();np.savez_compressed(stream,**a);arrays[tag+'.npz']=stream.getvalue()
        data['refinement']=dict(lineage=lineage,changes=changes,seconds=time.monotonic()-start,decoder_timeout=120,
            note='Same 4000 physical shots and acceptance masks. Only unresolved Bell syndromes re-decoded; known results unchanged. No added sample count.')
        (out/'results.json').write_text(json.dumps(data,indent=2)+'\n')
        with zipfile.ZipFile(out/'samples-circuits.zip','w',zipfile.ZIP_DEFLATED) as dest:
            for name in saved.namelist():dest.writestr(name,arrays.get(name,saved.read(name)))
        print(json.dumps(dict(changes=changes,remaining=[r['bell_any']['unknown'] for r in data['rows']])),flush=True)


if __name__=='__main__':main()
