"""Branch-exact reference circuits and piecewise-constant drive response."""

import itertools
import json
from pathlib import Path

import numpy as np


IDENTITY = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], complex)
Y = np.array([[0, -1j], [1j, 0]], complex)
Z = np.diag([1.0, -1.0]).astype(complex)
PAULI = np.stack((X, Y, Z))


def gate(theta, phi, lam):
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -np.exp(1j * lam) * s],
                     [np.exp(1j * phi) * s, np.exp(1j * (phi + lam)) * c]])


def single(vector, index, matrix):
    pairs = [(i, i | (1 << index)) for i in range(len(vector)) if not (i >> index) & 1]
    result = vector.copy()
    for pair in pairs:
        address = list(pair)
        result[address] = matrix @ vector[address]
    return result


def branch_measure(branches, qubit, memory, register):
    branches_out = []
    for weight, state, mem, reg in branches:
        basis = np.arange(len(state))
        for bit in (0, 1):
            measured = np.where((basis >> qubit) & 1 == bit, state, 0)
            prob = float(np.vdot(measured, measured).real)
            if prob <= 1e-26:
                continue
            recorded = {**mem, memory: bit}
            flags = {**reg, register: bit} if register is not None else reg.copy()
            branches_out.append((weight * prob, measured / np.sqrt(prob), recorded, flags))
    return branches_out


def simulate(instructions, qubits, initial=None, injected=()):
    vector = np.zeros(2**qubits, complex)
    vector[:2] = [1, 0] if initial is None else initial
    branches = [(1.0, vector, {}, {})]
    for step, inst in enumerate(instructions):
        if step == 3 and injected:
            for target in injected:
                branches = [(p, single(v, target, X), m, r) for p, v, m, r in branches]
        name = inst["name"]
        if name == "measure":
            regs = inst.get("register", [None] * len(inst["qubits"]))
            for qubit, slot, reg in zip(inst["qubits"], inst["memory"], regs, strict=True):
                branches = branch_measure(branches, qubit, slot, reg)
            continue
        new_branches = []
        for weight, state, memory, regs in branches:
            flags = regs.copy()
            if "conditional" in inst and not flags[inst["conditional"]]:
                new_branches.append((weight, state, memory, flags))
                continue
            if name == "bfunc":
                assert inst["relation"] == "=="
                encoded = sum(b << i for i, b in flags.items())
                target = inst["register"]
                if isinstance(target, list):
                    target, = target
                flags[target] = int(encoded & int(inst["mask"], 16) == int(inst["val"], 16))
            elif name == "cx":
                c, t = inst["qubits"]
                perm = [i ^ (1 << t) if (i >> c) & 1 else i for i in range(len(state))]
                state = state[perm]
            elif name in {"u1", "u2", "u3"}:
                angles = inst["params"]
                if name == "u1":
                    angles = [0, 0, *angles]
                elif name == "u2":
                    angles = [np.pi / 2, *angles]
                state = single(state, inst["qubits"][0], gate(*angles))
            else:
                raise ValueError(f"Unhandled instruction {name}")
            new_branches.append((weight, state, memory, flags))
        branches = new_branches
    return branches


def outcomes(branches):
    output = {}
    for p, _, memory, _ in branches:
        k = hex(sum(bit << i for i, bit in memory.items()))
        output[k] = output.get(k, 0.0) + p
    return output


def circuits(src):
    result = {k: outcomes(simulate(src[k]["instructions"], 2)) for k in ("J27", "J28")}
    initial_states = [[1, 0], [0, 1], [2**-0.5, 1j * 2**-0.5], [np.sqrt(.3), np.exp(.7j)*np.sqrt(.7)]]
    teleport = []
    prep = src["J33"]["instructions"][0]["params"]
    for initial in initial_states:
        desired = gate(np.pi / 2, *prep) @ initial
        control = simulate(src["J33"]["instructions"], 3, initial=initial)
        fidelities = {}
        for p, state, mem, _ in control:
            rho = state.reshape(2, 4) @ state.reshape(2, 4).conj().T
            fidelities[hex(sum(bit << i for i, bit in mem.items()))] = [p, float(np.vdot(desired, rho @ desired).real)]
        teleport.append(fidelities)
    result["teleportation"] = teleport
    rep = {}
    for pattern in itertools.product((0, 1), repeat=3):
        faults = [i for i, b in enumerate(pattern) if b]
        observed = outcomes(simulate(src["J37"]["instructions"], 5, injected=faults))
        syndrome = (pattern[0] ^ pattern[1]) | ((pattern[1] ^ pattern[2]) << 1)
        desired = {hex(syndrome): .5, hex(28 | syndrome): .5}
        rep["".join(map(str, pattern))] = dict(p_out=observed, expected=desired, syndrome=syndrome,
                                             logical_flip=len(faults) >= 2)
    result["repetition"] = rep
    result["repetition_logical_error"] = {str(p): sum(p**sum(bits) * (1-p)**(3-sum(bits))
             for bits in itertools.product((0, 1), repeat=3) if sum(bits) >= 2)
             for p in (.01, .03, .05, .10)}
    return result


def pair(x):
    return np.asarray(x, dtype=float) @ np.array([1.0, 1.0j])


def pulse_layout(items, library, level):
    """Reconstruct occupied windows and causal feedback, separately from JSON schema."""
    assert [i["t0"] for i in items] == sorted(i["t0"] for i in items)
    windows, regs, frame, phases, readouts = {}, {}, {}, [], []
    for item in items:
        name, start = item["name"], item["t0"]
        assert type(start) is int and start >= 0
        if "conditional" in item:
            assert level == 2 and regs[item["conditional"]] <= start
        if name == "acquire":
            assert item["duration"] > 0
            assert len(item["memory_slot"]) == len(item["qubits"])
            end = start + item["duration"]
            if "register_slot" in item:
                assert level == 2 and len(item["register_slot"]) == len(item["qubits"])
                regs.update({i: end for i in item["register_slot"]})
            readouts.append([start, end, item["memory_slot"]])
        else:
            ch = item["ch"]
            assert ch[0] in "dmu" and ch[1:].isdigit()
            if name == "fc":
                frame[ch] = frame.get(ch, 0.0) + item["phase"]
            elif name == "pv":
                assert abs(complex(*item["val"])) <= 1
            else:
                assert start >= windows.get(ch, 0)
                windows[ch] = start + library[name]
                phases.append([ch, start, -frame.get(ch, 0.0)])
    return dict(channel_end=windows, acquisition=readouts, phase_rad=phases)


def pulse_protocol(src):
    library = {x["name"]: pair(x["samples"]) for x in src["J76"]["pulse_library"]}
    durations = {k: len(v) for k, v in library.items()}
    demo_durations = {"pulse1": 10, "drag_pulse": 10, "square_pulse": 10}
    rabi = [pulse_layout(x["instructions"], durations, 2) for x in src["J77"]]
    t1 = [pulse_layout(x["instructions"], durations, 1) for x in src["J84"]]
    try:
        pulse_layout(src["J56"], demo_durations, 1)
    except (AssertionError, KeyError):
        level1_feedback_rejected = True
    else:
        level1_feedback_rejected = False
    area_ratio = float((library["pulse1"].sum() / library["pulse2"].sum()).real)
    return dict(rabi=rabi, durations=durations, t1=t1,
        t1_wait_from_pulse_end={exp["header"]["name"]: o["acquisition"][0][0] - o["channel_end"]["d0"]
                              for exp, o in zip(src["J84"], t1, strict=True) if "d0" in o["channel_end"]},
        J55=pulse_layout(src["J55"], demo_durations, 2),
        J56=pulse_layout(src["J56"], demo_durations, 2), level1_feedback_rejected=level1_feedback_rejected,
        rabi_area_ratio=area_ratio, rabi_ideal_p1=[0.0, float(np.sin(np.pi * area_ratio / 2)**2), 1.0])


def rotation(axis, seconds):
    length = np.linalg.norm(axis)
    if length == 0:
        return IDENTITY.copy()
    a = length * np.asarray(seconds) / 2
    return (np.cos(a)[..., None, None] * IDENTITY
            - 1j * np.sin(a)[..., None, None] * np.einsum("k,kij->ij", axis, PAULI) / length)


def drive(samples, dt, epsilon=0.0, detuning=0.0):
    u = IDENTITY.copy()
    for sample in samples:
        a = [(1+epsilon)*sample.real, (1+epsilon)*sample.imag, detuning]
        u = rotation(np.asarray(a), dt) @ u
    return u


def x_error(u):
    return max(0.0, float(1.0 - abs(np.trace(X @ u) / 2)**2))


def response(samples, dt, frequencies, nodes=12):
    """Integrate the toggling-frame Pauli coefficients of Z/2 and drive/2."""
    roots, weights = np.polynomial.legendre.leggauss(nodes)
    seconds = dt * (roots+1) / 2
    w = dt * weights / 2
    u = IDENTITY.copy()
    out = np.zeros((2, len(frequencies), 3), complex)
    for i, sample in enumerate(samples):
        axis = np.array([sample.real, sample.imag, 0.0])
        evolution = rotation(axis, seconds) @ u if np.any(axis) else np.repeat(u[None], nodes, axis=0)
        terms = np.stack((Z/2, np.einsum("k,kij->ij", axis, PAULI) / 2))
        toggled = evolution.conj().transpose(0, 2, 1)[None] @ terms[:, None] @ evolution[None]
        coeff = np.einsum("knij,pji->knp", toggled, PAULI).real / 2
        phase = np.exp(2j * np.pi * frequencies[:, None] * (i*dt + seconds[None]))
        out += np.einsum("fn,knp,n->kfp", phase, coeff, w)
        u = rotation(axis, dt) @ u
    return np.sum(abs(out)**2, axis=2)


def filters(src):
    dt = 1e-6
    f = np.r_[0.0, np.logspace(0, 6, 601)]
    normalized = {x["name"]: pair(x["samples"]) for x in src["J73"]}
    w = normalized["walsh_gaussian"]
    b = normalized["BB1_gaussian"]
    calibrated = {"benchmark": np.full(len(w), np.pi/(len(w)*dt), dtype=complex)}
    orders = {}
    for turns in (1, 3, 5, 7, 9):
        control = w * (turns * np.pi / (dt*w.real.sum()))
        orders[str(turns)] = float(response(control, dt, np.array([0.0]))[0, 0])
        if turns == 3:
            calibrated["Walsh"] = control
    calibrated["BB1"] = b * (np.pi/(dt*b[:10].real.sum()))
    metrics = {}
    for name, u in calibrated.items():
        noise = response(u, dt, f)
        convergence = response(u, dt, f, nodes=24)
        metrics[name] = dict(dephasing=noise[0].tolist(), amplitude=noise[1].tolist(),
              quadrature_max_abs=(np.max(abs(noise-convergence), axis=1)).tolist(),
              x_error=x_error(drive(u, dt)),
              x_error_detuned=x_error(drive(u, dt, detuning=.01*np.pi/(40*dt))),
              x_error_amp1pct=x_error(drive(u, dt, epsilon=.01)),
              segment_angles_pi=(np.sum(abs(u).reshape(4, 10), axis=1)*dt/np.pi).tolist())
    primitive = np.full(10, np.pi/(10*dt), dtype=complex)
    sample = response(primitive, dt, f)
    inferred = dict(dephasing=(4*sample[0]).tolist(), amplitude=sample[1].tolist(), duration_us=10,
                    dephasing_operator="Z", amplitude_operator="drive/2")
    amp_b = np.angle(b)/np.pi
    time_domain = {k: dict(amplitude=(abs(v)/max(abs(v))).tolist(),
        phase_pi=np.where(abs(v) > 0, np.angle(v)/np.pi, 0.0).tolist()) for k, v in normalized.items()}
    return dict(dt_s=dt, frequency_hz=f.tolist(), time_domain=time_domain, rotations=metrics,
                inferred_benchmark=inferred, walsh_odd_turn_dc=orders, BB1_nonzero_phase_pi=[float(np.mean(amp_b[i+1:i+9])) for i in range(0,40,10)])


def main():
    src = json.loads(Path("config/examples-input.json").read_text())
    out = dict(circuits=circuits(src), pulse=pulse_protocol(src), figure4=filters(src))
    Path("results").mkdir(exist_ok=True)
    Path("results/model.json").write_text(json.dumps(out, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()

