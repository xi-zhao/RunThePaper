"""Declared SD6 timing variants; no paper numeric/reference input.

The v2 circuit remains the original baseline. Fresh ancilla / cross-stage
overlap variants test physical timing choices, not an identified author circuit.
All live idle channels are retained unless an explicitly named ablation is used.
"""
from pathlib import Path
import json
import hashlib
import time
import numpy as np
import stim
from simulate_sd6_factory_v2 import factory, dem_arrays
from structured_schedule import structured_tri


def timing_circuit(model, p, pccz, variant="baseline", only=None, omit=None):
    ideal, _, meta = factory(model, 0, 0, tri_override=structured_tri(model, (0, 2, 1, 3)))
    n = meta["n3"]
    old = meta["layers"]
    layers = [[] for _ in old]
    for k, layer in enumerate(old):
        for op in layer["operations"]:
            layers[k].append((layer["name"], op["gate"], op["targets"]))
    # Tail contains exactly the same records, postselection and ideal readout.
    tail = stim.Circuit()
    tick = 0
    for op in ideal:
        if tick >= len(old):
            tail.append(op)
        if op.name == "TICK":
            tick += 1
    fresh = variant != "baseline"
    if fresh:
        if variant not in ("fresh_strict", "fresh_overlap", "fresh_aligned"):
            raise ValueError(variant)
        S = list(range(n, 2*n))
        F = list(range(meta["total_qubits"], meta["total_qubits"]+n))
        layers = [[] for _ in range(32)]
        dq = len(meta["quad_layers"])
        shift = dq-6 if variant == "fresh_aligned" else 0
        tri_start = shift
        # These are physical preparation operations, not noiseless fresh atoms.
        layers[tri_start].append(("tri_initialize", "R", list(range(n))+S))
        layers[tri_start+1].append(("tri_prepare_plus", "H", list(range(n))))
        layers[0].append(("quad_initialize", "R", list(range(2*n, meta["total_qubits"]))))
        layers[1].append(("quad_prepare_plus", "H", list(range(4*n, meta["total_qubits"]))))
        for k, pairs in enumerate(meta["tri_layers"]):
            layers[tri_start+2+k].append(("tri_syndrome", "CX", [v for a,d in pairs for v in (d,n+a)]))
        for k, pairs in enumerate(meta["quad_layers"]):
            layers[2+k].append(("quad_syndrome", "CX", [v for a,d in pairs for v in (4*n+a,2*n+d)]))
        tm = tri_start+6
        layers[tm].append(("tricycle_syndrome_readout", "M", S))
        tf = tm+1 if variant == "fresh_strict" else tm
        layers[tf-1].append(("fresh_fanout_initialize", "R", F))
        layers[tf].append(("fanout", "CX", [v for t,f in zip(range(n), F) for v in (t,f)]))
        layers[tf+1].append(("ccz_marginal", "DEPOLARIZE1", list(range(n))+F))
        layers[dq+2].append(("quad_H", "H", list(range(4*n, meta["total_qubits"]))))
        layers[dq+3].append(("quad_readout", "M", list(range(4*n, meta["total_qubits"]))))
        te = max(tf+2, dq+4 if variant == "fresh_strict" else dq+2)
        layers[te].append(("escape", "CX", [v for t,q in zip(range(n), range(3*n,4*n)) for v in (t,q)]))
        layers[te+1].append(("tricycle_H", "H", list(range(n))+F))
        layers[te+2].append(("tricycle_readout", "M", list(range(n))+F))
        layers = layers[:te+3]
    else:
        F = list(range(n, 2*n))
    circuit = stim.Circuit()
    live = set()
    program = []
    event_counts = {}
    for k, ops in enumerate(layers):
        acted = set()
        def noise(gate, qs, probability, category, stage):
            group = category+":"+stage
            event_counts[group] = event_counts.get(group, 0)+len(qs)//(2 if gate=="DEPOLARIZE2" else 1)
            enabled = (only is None or category in only or group in only) and not (omit and (category in omit or group in omit))
            if qs and probability and enabled:
                circuit.append(gate, qs, probability)
        for name, gate, targets in ops:
            assert not acted.intersection(targets), (variant,k,name)
            acted.update(targets)
            if gate == "R":
                live.update(targets)
                circuit.append(gate, targets)
                noise("X_ERROR", targets, p, "reset", name)
            elif gate == "M":
                group = "measurement:"+name
                event_counts[group] = event_counts.get(group,0)+len(targets)
                enabled = (only is None or "measurement" in only or group in only) and not (omit and ("measurement" in omit or group in omit))
                circuit.append(gate, targets, p if enabled else 0)
            elif gate == "H":
                circuit.append(gate, targets)
                noise("DEPOLARIZE1", targets, p, "one_qubit", name)
            elif gate == "CX":
                circuit.append(gate, targets)
                noise("DEPOLARIZE2", targets, p, "two_qubit", name)
            elif gate == "DEPOLARIZE1":
                noise(gate, targets, 16*pccz/21, "ccz", name)
            else:
                raise ValueError(gate)
        idle = sorted(live-acted)
        noise("DEPOLARIZE1", idle, p, "idle", "tick_"+str(k))
        program.append(dict(tick=k,operations=[dict(stage=s,gate=g,targets=t) for s,g,t in ops],idle=idle,live=len(live)))
        circuit.append("TICK")
        for name, gate, targets in ops:
            if gate=="M" and (fresh or name in ("tricycle_readout", "ccz_marginal_and_quad_readout")):
                live.difference_update(targets)
    circuit += tail
    dem = circuit.detector_error_model(decompose_errors=False)
    return circuit, dem, dict(variant=variant,post_start=meta["post_start"],npost=meta["npost"],n3=n,n4=2*n,
        layers=program,event_counts=event_counts,peak_live=max(x["live"] for x in program),
        live_volume=sum(x["live"] for x in program),qubit_index_count=circuit.num_qubits)


def exact_acceptance(dem, meta):
    h, _, p = dem_arrays(dem)
    sel = h[meta["post_start"]:meta["npost"]]
    q = len(sel)
    if q>12:
        raise ValueError("Exact character enumeration restricted to <=12 detector rows")
    signatures = np.array([int.from_bytes(np.packbits(col,bitorder="little").tobytes(),"little") for col in sel.T],np.uint64)
    counts = np.zeros(1<<q)
    np.add.at(counts, signatures, np.log1p(-2*p))
    # Character transform of signature log factors, in O(q 2**q) work.
    walsh = counts.copy()
    for step in (1<<i for i in range(q)):
        blocks=walsh.reshape(-1,2*step)
        a=blocks[:,:step].copy(); b=blocks[:,step:].copy()
        blocks[:,:step]=a+b; blocks[:,step:]=a-b
    return float(np.exp((counts.sum()-walsh)/2).mean())


def main():
    cfg=json.loads(Path("config/timing-audit-v3.json").read_text())
    models=json.loads(Path("config/models.json").read_text())["pairs"]
    out=Path(cfg["output"]);out.mkdir(parents=True,exist_ok=True)
    results=[]; circuits={}; programs={}; start=time.monotonic()
    for n4 in cfg["n4"]:
        model=next(m for m in models if m["quad"][0]==n4)
        for variant in cfg["variants"]:
            for spec in cfg["noise_selections"]:
                c,d,meta=timing_circuit(model,cfg["p"],cfg["pccz"],variant,only=spec.get("only"),omit=spec.get("omit"))
                alpha=exact_acceptance(d,meta)
                tag=f"n{n4}_{variant}_{spec['name']}"
                row=dict(n4=n4,variant=variant,selection=spec["name"],acceptance=alpha,
                    peak_live=meta["peak_live"],live_volume=meta["live_volume"],circuit_sha256=hashlib.sha256(str(c).encode()).hexdigest())
                if spec["name"]=="all":
                    det=c.compile_detector_sampler(seed=cfg["seed"]+n4).sample(cfg["control_shots"])
                    k=int((~det[:,meta["post_start"]:meta["npost"]].any(axis=1)).sum())
                    row.update(control_shots=cfg["control_shots"],control_accepted=k,
                        control_z=(k/cfg["control_shots"]-alpha)/np.sqrt(alpha*(1-alpha)/cfg["control_shots"]))
                    programs[tag]=meta;circuits[tag]=str(c)
                results.append(row)
                print(json.dumps(row),flush=True)
    # Full SD6 gate-order sweep, holding four-layer structured coloring fixed.
    order_rows=[]
    import itertools
    for n4 in cfg["n4"]:
        model=next(m for m in models if m["quad"][0]==n4)
        for order in itertools.permutations(range(4)):
            c,d,m=factory(model,cfg["p"],cfg["pccz"],tri_override=structured_tri(model,order))
            order_rows.append(dict(n4=n4,tri_order=order,acceptance=exact_acceptance(d,m)))
    result=dict(rows=results,order_sweep=order_rows,wall_seconds=time.monotonic()-start,
        assumptions=["Variant comparisons keep all active and live idle SD6 noise at stated strengths.",
        "Fresh variants use additional physical ancillas with noisy reset; fresh_overlap overlaps old-ancilla readout with new fanout and quad ancilla H/M with escape/readout.",
        "fresh_aligned additionally delays tricycle initialization to align critical paths. These are declared scheduling alternatives, not identified author circuits.",
        "All terminal quad X readouts are ideal diagnostics and excluded from postselection.",
        "Exact finite-DEM expectation in float64 is not interval-certified arithmetic.",
        "Noise-selection ablations deliberately depart from full SD6; never promoted as paper reproduction."])
    (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"circuits.json").write_text(json.dumps(circuits,indent=2)+"\n")
    (out/"programs.json").write_text(json.dumps(programs,indent=2)+"\n")


if __name__=="__main__":
    main()
