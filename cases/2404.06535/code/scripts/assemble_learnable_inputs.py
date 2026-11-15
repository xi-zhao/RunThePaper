"""Build compact score inputs from the published numeric ZIP members."""

from concurrent.futures import ThreadPoolExecutor
import json
from http.client import IncompleteRead
from ssl import SSLError
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from urllib.error import HTTPError, URLError

import numpy as np
from scipy.sparse import csr_matrix, vstack

import fetch_features as archive
from read_features import load

SOURCE = Path("source/features")
BASE = "reference/layout-features.npz"
TIMES = "config/idle-exposures.npz"
GATES = "config/gate-factors.npz"
AUDIT = "checks/physical-input-reconstruction.json"
FIELDS = ("T1_times.pkl", "zz_phases.pkl", "Gamma1_couplings.pkl")


def fetch(row, temp):
    cached = SOURCE / row["name"]
    for attempt in range(3):
        try:
            receipt = archive.get_member(row)
            path = cached if cached.is_file() else temp / row["name"]
            return load(path), receipt
        except (HTTPError, URLError, TimeoutError, ConnectionError, SSLError, IncompleteRead) as exc:
            if attempt == 2:
                return None, dict(member=row["name"], failed=type(exc).__name__,
                                  code=getattr(exc,"code",None))
            sleep(2 * (attempt + 1))


def exposures_for_layout(t1, zz, gamma, default_t, default_z):
    t_exposure = None
    z_exposure = None
    mode = "fixed"
    error_t, error_z = None, None
    if t1 is not None:
        raw = np.array([v for ts in t1.values() for v in ts])
        modes = [("stored_ratio", raw)]
        if gamma is not None:
            scaled = np.array([v*gamma[q] for q, ts in t1.items() for v in ts])
            modes.append(("time_times_rate", scaled))
        for label, values in modes:
            if np.any(values < 0):
                continue
            u = -np.expm1(-values/2)
            base = np.prod(1-u/3-u*(2-u)/6)
            err = abs(base-default_t)
            error_t = err if error_t is None else min(error_t,err)
            if err<1e-8:
                mode,t_exposure = label,u
                break
    if zz is not None:
        phase = np.array([v for angles in zz.values() for v in angles])
        v = np.sin(phase/2)**2
        error_z = abs(np.prod(1-2*v/3)-default_z)
        if error_z<1e-8:
            z_exposure = v
    return t_exposure, z_exposure, mode, error_t, error_z


def concat(parts):
    return np.concatenate(parts) if parts else np.empty(0,np.float32)


def batch_features(batch, groups, offsets, features, coefficients, key_index, zip_rows, dest):
    selected=np.flatnonzero(groups[:,0]==batch)
    gates=load(SOURCE/batch/"gate_feature_dic.pkl")
    scores_t=load(SOURCE/batch/"t1_fidelity_dic.pkl")
    scores_z=load(SOURCE/batch/"zz_fidelity_dic.pkl")
    index=np.array([key_index[repr(k)] for k in coefficients])
    weights=-np.log(np.array(list(coefficients.values())))
    stat=dict(batch=batch,layouts=0,stored_ratio=0,time_times_rate=0,fixed=0,zz_verified=0,
              max_best_t1_abs_error=0.,max_zz_abs_error=0.,gate_max_abs_error=0.)
    rows,t,z=[],[],[]
    t_offsets,z_offsets=[0],[0]
    t_mask,z_mask=[],[]
    with TemporaryDirectory(prefix="qc15-physical-") as d:
        temp=Path(d)
        archive.ROOT=temp
        to_fetch=[]
        for f in FIELDS:
            target=temp/batch/f
            old=SOURCE/batch/f
            if old.is_file():
                target.parent.mkdir(parents=True,exist_ok=True)
                target.symlink_to(old.resolve())
            to_fetch.append(zip_rows[f"{batch}/{f}"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            retrieved=list(pool.map(lambda row:fetch(row,temp),to_fetch))
        (ts, zs, gamma), provenance=zip(*retrieved)
    for n in selected:
        i=int(groups[n,1])
        a,b=offsets[n:n+2]
        g=np.asarray(gates[i])
        assert g.shape==(b-a,len(coefficients))
        weighted=g*weights
        ii,jj=np.nonzero(weighted)
        rows.append(csr_matrix((weighted[ii,jj],(ii,index[jj])),shape=(b-a,len(key_index))))
        stat["gate_max_abs_error"]=max(stat["gate_max_abs_error"],
            float(np.max(abs(weighted.sum(axis=1)-features[a:b,:2].sum(axis=1)))))
        for j in range(b-a):
            layout_t=ts[i][j] if ts is not None and i in ts and len(ts[i])==b-a else None
            layout_z=zs[i][j] if zs is not None and i in zs and len(zs[i])==b-a else None
            u,v,mode,err_t,err_z=exposures_for_layout(
                layout_t,layout_z,gamma,scores_t[i][j],scores_z[i][j])
            stat["layouts"]+=1
            stat[mode]+=1
            stat["zz_verified"]+=int(v is not None)
            stat["max_best_t1_abs_error"]=max(stat["max_best_t1_abs_error"],err_t or 0.)
            stat["max_zz_abs_error"]=max(stat["max_zz_abs_error"],err_z or 0.)
            t_mask.append(u is not None)
            z_mask.append(v is not None)
            if u is not None:
                t.append(u.astype(np.float32))
            if v is not None:
                z.append(v.astype(np.float32))
            t_offsets.append(t_offsets[-1]+(len(u) if u is not None else 0))
            z_offsets.append(z_offsets[-1]+(len(v) if v is not None else 0))
    g=vstack(rows,format="csr")
    out=dest.with_suffix(".partial.npz")
    np.savez_compressed(out, data=g.data, indices=g.indices, indptr=g.indptr,
        shape=g.shape, t=concat(t),z=concat(z),t_offsets=t_offsets,z_offsets=z_offsets,
        t_mask=t_mask,z_mask=z_mask,stat=json.dumps(stat),receipts=json.dumps(provenance))
    out.replace(dest)
    print(batch,stat["layouts"],stat["stored_ratio"],stat["time_times_rate"],
          stat["zz_verified"],flush=True)


def main():
    with np.load(BASE, allow_pickle=False) as base:
        groups=base["group"]
        offsets=base["offsets"]
        features=base["x"]
    batches=sorted(set(groups[:,0]))
    zip_rows={r["name"]:r for r in json.loads(Path("checks/zip-index.json").read_text())}
    coefficients={batch:load(SOURCE/batch/"fidelities_dic.pkl") for batch in batches}
    keys=sorted({repr(k) for coef in coefficients.values() for k in coef})
    key_index={k:i for i,k in enumerate(keys)}
    cache=Path("config/physical-batches-v1")
    cache.mkdir(exist_ok=True)
    check,rows,receipts=[],[],[]
    t,z,t_mask,z_mask=[],[],[],[]
    t_offsets,z_offsets=[np.array([0])],[np.array([0])]
    for batch in batches:
        dest=cache/(batch+".npz")
        if not dest.exists():
            batch_features(batch,groups,offsets,features,coefficients[batch],key_index,zip_rows,dest)
        with np.load(dest,allow_pickle=False) as b:
            check.append(json.loads(str(b["stat"])))
            receipts.extend(json.loads(str(b["receipts"])))
            rows.append(csr_matrix((b["data"],b["indices"],b["indptr"]),shape=tuple(b["shape"])))
            t.append(b["t"]); z.append(b["z"])
            t_mask.append(b["t_mask"]); z_mask.append(b["z_mask"])
            t_offsets.append(b["t_offsets"][1:]+t_offsets[-1][-1])
            z_offsets.append(b["z_offsets"][1:]+z_offsets[-1][-1])
    g=vstack(rows,format="csr")
    assert g.shape[0]==len(features)==sum(len(m) for m in t_mask)==sum(len(m) for m in z_mask)
    assert max(x["gate_max_abs_error"] for x in check)<2e-6
    t_values,z_values=concat(t),concat(z)
    assert t_values.size*4+z_values.size*4 < 90*1024**2
    np.savez_compressed(GATES, data=g.data, indices=g.indices, indptr=g.indptr,
                        shape=g.shape, gate_names=np.asarray(keys))
    np.savez_compressed(TIMES, t=t_values, z=z_values, t_mask=concat(t_mask), z_mask=concat(z_mask),
                        t_offsets=concat(t_offsets),z_offsets=concat(z_offsets))
    Path(AUDIT).write_text(json.dumps(dict(batches=check, members=receipts, gate_terms=len(keys),
         t_exposures=t_values.size,z_exposures=z_values.size,
         matching_tolerance=1e-8, fallback="Keep the released aggregate score for unmatched layouts."),
         ensure_ascii=False,indent=2)+"\n")


if __name__ == "__main__":
    main()
