"""Circuit-derived preparation frame posterior; no source-result inputs.

The training-only ideal MPP labels the quad X stabilizers at the pre-escape
boundary. It is never available to the operational decoder or postselection.
The full circuit retains all SD6 channels, including subsequent quad faults.
"""
from contextlib import contextmanager
import hashlib
import heapq
import json
from pathlib import Path
import sys
import time
import numpy as np
import stim
import audit_sd6_timing_v3 as timing
from simulate_sd6_factory_v2 import factory, edge_color, dem_arrays
from generate_algebra import construct, nullspace
from structured_schedule import structured_tri

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def gate_order(model, order):
    """A fixed declared coloring/order, never selected by source acceptance."""
    hx = construct(model)[0]
    quad = edge_color(hx, order['quad_seed'])
    if order.get('reverse_quad', False):
        quad = quad[::-1]
    tri = structured_tri(model, tuple(order['tri']))
    old = timing.factory
    def chosen(*args, **kwargs):
        kwargs['quad_override'] = quad
        kwargs['tri_override'] = tri
        return factory(*args, **kwargs)
    timing.factory = chosen
    try:
        yield
    finally:
        timing.factory = old


def full_factory(model, p, pccz, schedule, order):
    with gate_order(model, order):
        c, dem, meta = timing.timing_circuit(model, p, pccz, schedule)
    return c, dem, meta


def select_preparation_noise(circuit, model, meta, preparation):
    """Keep the same ideal gates; retain one independent subset of channels.

    This is a diagnostic factorization only. Production always uses full SD6.
    """
    hx = construct(model)[0]; n = meta['n3']
    quad = set(range(2*n,4*n)); anc = set(range(4*n,4*n+len(hx)))
    owned = quad | anc
    boundary = next(l['tick'] for l in meta['layers']
                    if any(o['stage']=='escape' for o in l['operations']))
    out = stim.Circuit(); tick = 0
    for op in circuit:
        name, targets, args = op.name, op.targets_copy(), op.gate_args_copy()
        if name in ('X_ERROR', 'DEPOLARIZE1', 'DEPOLARIZE2'):
            width = 2 if name=='DEPOLARIZE2' else 1
            kept = []
            for i in range(0,len(targets),width):
                group = targets[i:i+width]; ids = [t.value for t in group]
                is_prep = all(x in owned for x in ids) and all(x in anc or tick<boundary for x in ids)
                if is_prep == preparation: kept.extend(group)
            if kept: out.append(name, kept, args)
        elif name in ('M','MX') and args and args[0]:
            for t in targets:
                is_prep = t.value in anc
                out.append(name, [t], args[0] if is_prep==preparation else 0)
        else:
            out.append(op)
        if name=='TICK': tick += 1
    return out


def prep_circuit(model, p, meta):
    hx, _, _, _, tx, _ = construct(model)
    n = tx.shape[1]; q = len(tx)
    quad = set(range(2*n, 4*n)); anc = set(range(4*n, 4*n+len(hx)))
    owned = quad | anc
    boundary = next(layer['tick'] for layer in meta['layers']
                    if any(op['stage']=='escape' for op in layer['operations']))
    c = stim.Circuit(); records = {}; measured = 0
    def primitive(g, qs):
        nonlocal measured
        if g=='M':
            c.append('M', qs, p)
            for qubit in qs:
                records[qubit] = measured; measured += 1
        else:
            c.append(g, qs)
            channel = {'R':'X_ERROR', 'H':'DEPOLARIZE1', 'CX':'DEPOLARIZE2'}[g]
            if p: c.append(channel, qs, p)
    for layer in meta['layers']:
        tick = layer['tick']
        for op in layer['operations']:
            g, qs = op['gate'], op['targets']
            if g=='DEPOLARIZE1': continue  # CCZ is outside quad preparation.
            if g=='CX':
                selected = [x for pair in zip(qs[::2], qs[1::2])
                            if set(pair)<=owned for x in pair]
                if selected:
                    assert tick < boundary, 'Ancilla-Q coupling beyond preparation boundary'
                    primitive(g, selected)
            else:
                selected = [x for x in qs if x in anc or (x in quad and tick < boundary)]
                if selected: primitive(g, selected)
        idles = [x for x in layer['idle'] if x in anc or (x in quad and tick < boundary)]
        if idles and p: c.append('DEPOLARIZE1', idles, p)
        c.append('TICK')
    assert set(records) == anc
    m = nullspace(hx.T)
    for row in m:
        c.append('DETECTOR', [stim.target_rec(records[4*n+i]-measured)
                             for i in np.flatnonzero(row)])
    for j in range(q):
        terms = []
        for x in np.flatnonzero(hx[3*q+j]):
            if terms: terms.append(stim.target_combiner())
            terms.append(stim.target_x(2*n+int(x)))
        c.append('MPP', terms); measured += 1
        # Unobserved frame label only; operational input is metachecks S alone.
        c.append('OBSERVABLE_INCLUDE', [stim.target_rec(records[4*n+3*q+j]-measured),
                                       stim.target_rec(-1)], j)
    dem = c.detector_error_model(decompose_errors=False)
    return c, dem, dict(boundary=boundary, metachecks=len(m), frame_bits=q)


def row_compression(h):
    """Independent row basis in input order, and original-row coordinates."""
    h = np.asarray(h, dtype=np.uint8)
    basis = []; selected = []; maps = []
    for row_id, row in enumerate(h):
        v = row.copy(); combination = 0
        for pivot, reduced, coordinates in basis:
            if v[pivot]: v ^= reduced; combination ^= coordinates
        nz = np.flatnonzero(v)
        if len(nz):
            unit = 1 << len(selected)
            selected.append(row_id)
            basis.append((int(nz[0]), v, combination ^ unit))
            maps.append(unit)
        else:
            maps.append(combination)
    # Exact GF(2) reconstruction is checked, not assumed from rank alone.
    selected_h = h[selected]
    for row, mask in zip(h, maps):
        ids = [i for i in range(len(selected)) if (mask >> i) & 1]
        recovered = np.bitwise_xor.reduce(selected_h[ids], axis=0) if ids else np.zeros(h.shape[1], np.uint8)
        assert np.array_equal(row, recovered)
    return selected_h, selected, np.asarray(maps, np.uint64)


def fwht(a):
    for step in (1 << i for i in range(a.size.bit_length()-1)):
        b = a.reshape(-1, 2*step)
        x = b[:, :step].copy()
        np.subtract(x, b[:, step:], out=b[:, :step])
        np.add(x, b[:, step:], out=b[:, step:])
        # Restore sum first, difference second; bounded temporary memory.
        x[:] = b[:, :step]
        b[:, :step] = b[:, step:]
        b[:, step:] = x
    return a


def joint_distribution(h, probabilities, syndrome_bits):
    compressed, selected, maps = row_compression(h)
    rank = len(compressed)
    assert selected[:syndrome_bits] == list(range(syndrome_bits))
    if rank > 27: raise ValueError(f'Joint rank {rank} exceeds declared resource bound')
    keys = np.sum(compressed.astype(np.uint64) * (np.uint64(1) << np.arange(rank, dtype=np.uint64))[:, None], axis=0)
    assert np.all((probabilities>=0) & (probabilities<.5))
    spectrum = np.zeros(1 << rank)
    np.add.at(spectrum, keys, np.log1p(-2*probabilities))
    total = spectrum.sum(); fwht(spectrum)
    spectrum *= -.5; spectrum += total/2; np.exp(spectrum, out=spectrum)
    fwht(spectrum); spectrum /= len(spectrum)
    normalization = float(spectrum.sum()); minimum = float(spectrum.min())
    assert abs(normalization-1)<1e-10 and minimum > -1e-13, (normalization, minimum)
    table = spectrum.reshape(1 << (rank-syndrome_bits), 1 << syndrome_bits)
    return table, maps, dict(rank=rank, selected_rows=selected,
                            normalization=normalization, minimum_probability=minimum)


def full_frame_values(syndromes, coordinates, frame_maps, syndrome_bits):
    key = np.asarray(syndromes, np.uint64) | (np.asarray(coordinates, np.uint64) << np.uint64(syndrome_bits))
    frame = np.zeros(key.shape, np.uint64)
    for i, mask in enumerate(frame_maps):
        parity = np.zeros(key.shape, np.uint64)
        for j in range(int(mask).bit_length()):
            if (int(mask)>>j)&1: parity ^= (key >> np.uint64(j)) & np.uint64(1)
        frame |= parity << np.uint64(i)
    return frame


def make_decoder(model, p, meta):
    c, dem, info = prep_circuit(model, p, meta)
    h, f, probabilities = dem_arrays(dem); m = len(h)
    if p == 0:
        # Only S=0 is reachable; values for impossible S are unused placeholders.
        frame = np.zeros(1 << m, np.uint64)
        mass = np.zeros(1 << m); mass[0] = 1.
        return frame, dict(info, rank=0, normalization=1., minimum_probability=0.,
            reachable_syndromes=1, classification_success=1.,
            unreachable_policy='zero placeholders; never operationally reached at p=0',
            circuit_sha256=hashlib.sha256(str(c).encode()).hexdigest(),
            observed_syndrome_probability=mass.tolist()), (c, dem)
    table, maps, stats = joint_distribution(np.vstack([h, f]), probabilities, m)
    best = table.argmax(axis=0)
    frame = full_frame_values(np.arange(1 << m), best, maps[m:], m)
    stats.update(info, classification_success=float(table.max(axis=0).sum()),
                 circuit_sha256=hashlib.sha256(str(c).encode()).hexdigest(),
                 observed_syndrome_probability=table.sum(axis=0).tolist())
    return frame, stats, (c, dem)


def frame_residual_distribution(dem, decoder):
    h, f, probabilities = dem_arrays(dem); m = len(h); q = len(f)
    table, maps, stats = joint_distribution(np.vstack([h,f]), probabilities, m)
    residual, marginal = residual_from_table(table, maps, decoder, m, q)
    return residual, marginal, stats


def residual_from_table(table, maps, decoder, m, q):
    by_s = full_frame_values(np.arange(1 << m), 0, maps[m:], m)
    by_c = full_frame_values(0, np.arange(len(table)), maps[m:], m)
    residual = np.zeros(1 << q); marginal = np.zeros(1 << q)
    for coordinate, row in zip(by_c, table):
        frames = (by_s ^ coordinate).astype(np.int64)
        marginal += np.bincount(frames, weights=row, minlength=1 << q)
        residual += np.bincount(frames ^ decoder.astype(np.int64), weights=row, minlength=1 << q)
    return residual, marginal


def mle_frame_decoder(dem):
    """Exact most-likely independent DEM-fault configuration for every S.

    Positive log-odds reduce syndrome MLE to a shortest-path problem on the XOR
    group. Repeating a mechanism twice cannot improve a path: it cancels with
    positive cost. Equal-syndrome mechanisms keep one fixed minimum-cost choice;
    this sums no degenerate classes and is explicitly distinct from frame MAP.
    """
    h, f, probabilities = dem_arrays(dem); m = len(h)
    edges = {}
    for index, p in enumerate(probabilities):
        syndrome = sum(int(x) << i for i,x in enumerate(h[:,index]))
        frame = sum(int(x) << i for i,x in enumerate(f[:,index]))
        if not syndrome: continue
        weight = float(np.log((1-p)/p))
        candidate = (weight, frame, index)
        if syndrome not in edges or candidate < edges[syndrome]: edges[syndrome] = candidate
    distance = np.full(1 << m, np.inf); distance[0] = 0
    frames = np.zeros(1 << m, np.uint64); queue = [(0.,0)]
    while queue:
        cost, s = heapq.heappop(queue)
        if cost != distance[s]: continue
        for delta, (weight, frame, _) in edges.items():
            target = s ^ delta; newcost = cost+weight
            if newcost < distance[target]-1e-12:
                distance[target] = newcost; frames[target] = int(frames[s]) ^ frame
                heapq.heappush(queue,(newcost,target))
    assert np.isfinite(distance).all()
    # Complete Bellman inequalities certify minimum cost for this finite graph.
    ids = np.arange(len(distance))
    max_slack = max(float(np.max(distance[ids ^ delta]-distance-weight))
                    for delta, (weight,_,_) in edges.items())
    assert max_slack < 1e-9
    return frames, dict(syndromes=len(frames), distinct_edges=len(edges),
                        max_cost=float(distance.max()), bellman_max_violation=max_slack,
                        tie_break='lowest weight, then frame integer, then DEM column; fixed Dijkstra node order')


def canonical_characters(h, probabilities):
    terms = {}
    for col, p in zip(h.T, probabilities):
        key = sum(int(x) << i for i,x in enumerate(col))
        if key: terms[key] = terms.get(key,0.)+float(np.log1p(-2*p))
    return terms


def factorization_check(full_dem, prep_dem, rest_dem, model, meta):
    """All nonzero character-signature factors, not a selected set of tests."""
    nt = len(nullspace(construct(model)[-1].T))
    h,_,p = dem_arrays(full_dem)
    full = canonical_characters(h[nt:meta['npost']],p)
    h,f,p = dem_arrays(prep_dem)
    prep = canonical_characters(np.vstack([h,f]),p)
    h,_,p = dem_arrays(rest_dem)
    rest = canonical_characters(h[nt:meta['npost']],p)
    keys = set(full)|set(prep)|set(rest)
    error = max(abs(full.get(k,0)-prep.get(k,0)-rest.get(k,0)) for k in keys)
    assert error<1e-12, error
    return dict(signatures=len(keys), max_log_character_factor_error=error)


def acceptance_joint(dem, model, meta, decoder):
    h, _, probs = dem_arrays(dem)
    tri_count = len(nullspace(construct(model)[-1].T))
    m = meta['post_start']-tri_count
    joint_h = h[tri_count:meta['npost']]
    table, maps, stats = joint_distribution(joint_h, probs, m)
    # Convert each full desired frame to the joint table's independent rows.
    selection = np.zeros(1 << m, np.int64)
    for j, row_id in enumerate(stats['selected_rows'][m:]):
        selection |= (((decoder >> np.uint64(row_id-m)) & np.uint64(1)).astype(np.int64) << j)
    reconstructed = full_frame_values(np.arange(1 << m), selection, maps[m:], m)
    valid = reconstructed == decoder
    masses = table[selection, np.arange(1 << m)] * valid
    stats.update(acceptance=float(masses.sum()),
                 raw_acceptance=float(table[0, 0]),
                 syndrome_only_acceptance_upper_bound=float(table.max(axis=0).sum()),
                 frame_consistency_fraction=float(valid.mean()),
                 syndrome_marginal=table.sum(axis=0).tolist())
    # Raw event D=0 includes all S consistent with D=0, not just S=0.
    zero_decoder = np.zeros(1 << m, np.uint64)
    zero_coord = np.zeros(1 << m, np.int64)
    zero_reconstructed = full_frame_values(np.arange(1 << m), zero_coord, maps[m:], m)
    stats['raw_acceptance'] = float(table[zero_coord, np.arange(1 << m)][zero_reconstructed==zero_decoder].sum())
    return stats


def sample_acceptance(circuit, model, meta, decoder, shots, seed):
    tri_count = len(nullspace(construct(model)[-1].T))
    m = meta['post_start']-tri_count
    q = meta['npost']-meta['post_start']
    sampler = circuit.compile_detector_sampler(seed=seed)
    counts = dict(raw=0, repaired=0, raw_and_repaired=0, repaired_with_tri_pass=0)
    for lo in range(0, shots, 100000):
        d = sampler.sample(min(shots-lo, 100000))
        s = np.sum(d[:, tri_count:meta['post_start']].astype(np.uint64) * (np.uint64(1) << np.arange(m, dtype=np.uint64)), axis=1)
        f = np.sum(d[:, meta['post_start']:meta['npost']].astype(np.uint64) * (np.uint64(1) << np.arange(q, dtype=np.uint64)), axis=1)
        raw = f==0; repaired = f==decoder[s]
        counts['raw'] += int(raw.sum()); counts['repaired'] += int(repaired.sum())
        counts['raw_and_repaired'] += int((raw & repaired).sum())
        counts['repaired_with_tri_pass'] += int((repaired & ~d[:, :tri_count].any(1)).sum())
    return dict(shots=shots, seed=seed, counts=counts)


if __name__ == '__main__':
    model = json.loads((ROOT/'config/models.json').read_text())['pairs'][int(sys.argv[1]) if len(sys.argv)>1 else 0]
    order = dict(quad_seed=100001, tri=[0,2,1,3])
    started = time.monotonic()
    c, dem, meta = full_factory(model,.001,.002,'fresh_aligned',order)
    decoder, stats, _ = make_decoder(model,.001,meta)
    print(json.dumps({k:v for k,v in stats.items() if k!='observed_syndrome_probability'}), flush=True)
    exact = acceptance_joint(dem,model,meta,decoder)
    print(json.dumps({k:v for k,v in exact.items() if k!='syndrome_marginal'}), flush=True)
    print(json.dumps(sample_acceptance(c,model,meta,decoder,100000,9831)), flush=True)
    print('seconds',time.monotonic()-started)
