"""Independent group-algebra construction and exact logical-state checks.

Only model definitions are inputs. No source plots or author code are read.
Distance and circuit error rates are deliberately not inferred from ranks.
"""
import itertools as it
import json
import math
import time
from pathlib import Path
import numpy as np


def bits(row):
    return sum(1 << int(j) for j in np.flatnonzero(row))


def echelon(rows):
    piv = {}
    for x in rows:
        x = int(x)
        while x:
            p = x.bit_length() - 1
            if p in piv:
                x ^= piv[p]
            else:
                piv[p] = x
                break
    return piv


def rank(a):
    return len(echelon(bits(r) for r in a))


def nullspace(a):
    a = np.array(a, dtype=np.uint8, copy=True)
    m, n = a.shape
    r = 0
    piv = []
    for c in range(n):
        loc = np.flatnonzero(a[r:, c])
        if not len(loc):
            continue
        k = r + loc[0]
        a[[r, k]] = a[[k, r]]
        other = np.flatnonzero(a[:, c])
        other = other[other != r]
        a[other] ^= a[r]
        piv.append(c)
        r += 1
        if r == m:
            break
    free = [c for c in range(n) if c not in piv]
    out = np.zeros((len(free), n), dtype=np.uint8)
    for j, f in enumerate(free):
        out[j, f] = 1
        out[j, piv] = a[:r, f]
    return out


def logical_basis(check, stabilizer):
    base = list(stabilizer)
    old = rank(stabilizer)
    out = []
    for v in nullspace(check):
        new = rank(np.array(base + [v], dtype=np.uint8))
        if new > old:
            base.append(v)
            out.append(v)
            old = new
    return np.array(out, dtype=np.uint8)


def regular(group, terms):
    coords = list(it.product(*(range(l) for l in group)))
    index = {c: i for i, c in enumerate(coords)}
    m = np.zeros((len(coords), len(coords)), dtype=np.uint8)
    for j, c in enumerate(coords):
        for t in terms:
            moved = tuple((x + y) % l for x, y, l in zip(c, t, group))
            m[index[moved], j] ^= 1
    return m


def construct(model):
    a, b, c, d = [regular(model['group'], t) for t in model['polynomials']]
    z = np.zeros_like(a)
    hx = np.block([[c.T,z,b.T,d.T,z,z], [z,c.T,a.T,z,d.T,z],
                   [a.T,b.T,z,z,z,d.T], [z,z,z,a.T,b.T,c.T]])
    hz = np.block([[b,a,c,z,z,z], [d,z,z,c,z,a], [z,d,z,z,c,b], [z,z,d,b,a,z]])
    mx = np.hstack([a.T,b.T,c.T,d.T])
    mz = np.hstack([d,b,a,c])
    tx = np.hstack([a.T,b.T,c.T])
    tz = np.block([[c,z,a], [z,c,b], [b,a,z]])
    return hx,hz,mx,mz,tx,tz


def main():
    start = time.monotonic()
    cfg = json.loads(Path('config/models.json').read_text())
    results = []
    arrays = {}
    for model in cfg['pairs']:
        hx,hz,mx,mz,tx,tz = construct(model)
        n = hx.shape[1]
        txlogical = logical_basis(tz, tx)
        # CNOT control -> target X supports extend into the last three sectors.
        embedded = np.hstack([np.zeros_like(txlogical),txlogical])
        coordinates = list(it.product(*(range(l) for l in model['group'])))
        ix = {c:i for i,c in enumerate(coordinates)}
        inv = [ix[tuple((-x)%l for x,l in zip(c,model['group']))] for c in coordinates]
        ng = len(inv)
        # Complementary pairs of {a,b,c,d}, in the paper's column order
        # bd, ad, cd, bc, ac, ab. A naive consecutive half-swap is wrong.
        swapinv = np.array([sector*ng+j for sector in [4,3,5,1,0,2] for j in inv])
        row = {'n3':tx.shape[1], 'n4':n, 'k3':tx.shape[1]-rank(tx)-rank(tz),
               'k4':n-rank(hx)-rank(hz), 'rank_hx4':rank(hx), 'rank_hz4':rank(hz),
               'css_orthogonality4':int(np.count_nonzero((hx@hz.T)%2)),
               'css_orthogonality3':int(np.count_nonzero((tx@tz.T)%2)),
               'metacheck_x_residual':int(np.count_nonzero((mx@hx)%2)),
               'metacheck_z_residual':int(np.count_nonzero((mz@hz)%2)),
               'check_weights_x':np.unique(hx.sum(1)).astype(int).tolist(),
               'check_weights_z':np.unique(hz.sum(1)).astype(int).tolist(),
               'embedded_logical_x_rank':rank(np.vstack([hx,embedded]))-rank(hx),
               'embedded_cycles_residual':int(np.count_nonzero((hz@embedded.T)%2)),
               'hadamard_inversion_swap_rowspace_rank':rank(np.vstack([hz,hx[:,swapinv]])),
               'source_nominal_distance':model['quad'][2], 'distance_verified':False}
        results.append(row)
        for key,a in zip(['hx','hz','mx','mz','tx','tz'],[hx,hz,mx,mz,tx,tz]):
            arrays[f'{n}_{key}']=a
        print(json.dumps(row),flush=True)

    # Enumerate all 2^9 computational amplitudes and all eight gauge outcomes.
    cells = list(it.product(range(3),range(3)))
    ci = {v:i for i,v in enumerate(cells)}
    permutations = list(it.permutations(range(3)))
    groups = [[(0,1),(1,2),(2,0)],[(0,2),(1,0),(2,1)]]
    errors = []
    outcomes = []
    for mu in it.product([0,1],repeat=3):
        mismatch = 0
        for free in it.product([0,1],repeat=6):
            q = dict(zip([c for c in cells if c[0]!=c[1]],free))
            q.update({(i,i):mu[i] for i in range(3)})
            determinant = sum(q[(p[0],0)]*q[(p[1],1)]*q[(p[2],2)] for p in permutations)%2
            expected = sum(math.prod(q[c] for c in g) for g in groups)%2
            correction = 0
            for a in range(3):
                if mu[a]:
                    b,c = [i for i in range(3) if i!=a]
                    correction ^= (q[(b,b)]*q[(c,c)]) ^ (q[(b,c)]*q[(c,b)])
            mismatch += determinant != ((expected+correction)%2)
        outcomes.append({'gauge_outcome':list(mu),'checked_amplitudes':64,'phase_mismatches':mismatch,
                         'measurement_probability':0.125})
    # Marginals and correlations of the 63 nonidentity three-qubit Paulis.
    paulis = [x for x in it.product(range(4),repeat=3) if x!=(0,0,0)]
    marginal_counts = [sum(p[0]==j for p in paulis) for j in range(4)]
    # P(all three no bit flip) != product of single-leg no-bit-flip probabilities.
    p = 0.002
    no_x_all = 1-p+p*sum(all(t in [0,3] for t in x) for x in paulis)/63
    no_x_one = 1-p*sum(x[0] in [1,2] for x in paulis)/63
    noise = {'nonidentity_paulis':len(paulis),'single_leg_counts_I_X_Y_Z':marginal_counts,
             'single_leg_depolarizing_ratio':sum(marginal_counts[1:])/63,
             'source_ratio':16/21,
             'illustrative_3leg_no_bitflip':no_x_all,
             'product_of_marginal_no_bitflip':no_x_one**3,
             'warning':'The last two values are a channel correlation diagnostic, not factory yield.'}
    stages = [972,1890,243,162,243,324]
    resources = {'small_factory_raw_volume':sum(stages),
                 'source_table_cost_ratios':[80400/4300,162800/4300,83800/8600,2286000/67000],
                 'ratio_provenance':'Arithmetic of published table entries; underlying LERs not independently generated.',
                 'zero_failure_trials_for_95pct_upper_below_1e9':math.ceil(math.log(0.05)/math.log1p(-1e-9)),
                 'approx_accepted_trials_for_20pct_relative_95pct_at_1e9':1.96**2/(0.2**2*1e-9)}
    out = Path('outputs/data');out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'code_matrices.npz',**arrays)
    summary = {'pairs':results,'det_to_two_ccz':outcomes,'ccz_channel':noise,'resources':resources,
               'elapsed_seconds':time.monotonic()-start,
               'scope_limit':'No circuit-level failure probability or full-paper completion is claimed.'}
    (out/'algebra.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__=='__main__':main()
