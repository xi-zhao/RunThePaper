"""Independent accounting for the explicit models of Mundada et al."""
import math


def failure(event_error, count):
    """At least one failure under the independent event model."""
    return -math.expm1(count * math.log1p(-event_error))


def mid_resources(logical, mode, m, pump=1):
    homogeneous = mode == "baseline"
    processor = logical if homogeneous else m["processor"]
    n_edges = 2 * processor if homogeneous else 3
    d = m["distance"]
    dm = m["memory_distance"]
    qpu = processor * (1 + m["ancilla_per_data"]) * d*d
    t_factory = m["t_factories_per_lq"] * m["t_factory_tiles"] * processor * d*d
    clifford = 2*n_edges*d
    t_injection = 2*processor*d
    boundary = logical + 2*processor
    if mode == "STQM":
        stat = logical*d*d
        memory = 0
        links = boundary*d*d*(1+pump)
        local = 2*qpu+boundary*d*d
    elif mode == "RAQM":
        stat = 0
        memory = logical*(1+m["ancilla_per_data"])*dm*dm
        links = boundary*dm*(2+m["bell_buffers"]+pump)
        local = 2*(qpu+memory)+boundary*dm
    else:
        stat = memory = links = 0
        local = 2*(qpu+t_factory+clifford+t_injection)
    active = qpu+memory+clifford+t_injection+t_factory+links
    return dict(qpu=qpu,t_factory=t_factory,clifford=clifford,t_injection=t_injection,
                active=active,static=stat,memory=memory,links=links,total=active+stat,local=local)


def rsa_resources(architecture, r):
    name, n_cache, n_lts, n_transfer, code, use_adder = architecture
    n_qpu = r["processor"]
    d = r["distance"]
    factory_tiles = 4*d*d+2*d
    rows = {}
    rows["QPU"] = (2*n_qpu*d*d+2*n_qpu*d+2*n_qpu*factory_tiles,0,4*n_qpu*d*d,0,(2*n_qpu+n_cache)*d*d)
    rows["cache"] = (0,n_cache*d*d,n_cache*d*d,0,0)
    transfer_qubits = 2*n_transfer*d*d
    if code == "surface":
        ds = 9
        rows["LTS"] = (2*n_lts*ds*ds+transfer_qubits+2*n_lts*ds,
                       0,4*n_lts*ds*ds+2*transfer_qubits,0,n_transfer*d*d)
    if code == "gross":
        rows["LTS"] = (24*n_lts+transfer_qubits,0,48*n_lts+2*transfer_qubits,24*n_lts,n_transfer*d*d)
    if use_adder:
        n_a = r["accelerator"]
        rows["Adder"] = (2*n_a*d*d+12*factory_tiles,0,4*n_a*d*d,0,n_a*d*d)
    active,stat,local,nonlocal_c,links = [sum(col) for col in zip(*rows.values())]
    active += links
    return dict(name=name,active=active,static=stat,total=active+stat,local=local,
                nonlocal_c=nonlocal_c,links=links,contributions=rows)


def state_transfer(m, cycle_ratio, idle_cycles=0, physical_teleport_error=0.):
    d = m["surgery_distance"]
    p = m["p_logical"]
    p_mem = m["p_memory_logical"]
    cycle = m["time_qubit_s"]
    t = 2*d*cycle_ratio*cycle
    e = 2*d*(p_mem+cycle_ratio*p)+idle_cycles*p_mem
    trans_p = 2*p+(physical_teleport_error/m["p_threshold"])**((m["distance"]+1)/2)
    return dict(surgery_seconds=t,surgery_error_linear=e,transversal_seconds=2*cycle,
                transversal_error_linear=trans_p)


def idle_equivalence(p_a, p_b):
    """Ratio of cycle times for equal total survival, assuming fixed cycle errors."""
    return math.log1p(-p_b)/math.log1p(-p_a)


def rsa_runtime(repetitions, milliseconds, success_attempts, recovery, fidelity):
    contributions = [n*t/1000/86400 for n,t in zip(repetitions,milliseconds)]
    return sum(contributions)*success_attempts*recovery/fidelity, contributions


def route_example(m):
    p = m["p_logical"]
    cycle = m["time_qubit_s"]
    examples = {}
    for r in [1,50,1000]:
        st = state_transfer(m,r)
        qpu = p/cycle
        mem = m["p_memory_logical"]/(cycle*r)
        transfer = st["surgery_seconds"]
        cost = st["surgery_error_linear"]
        # Eq. (1) with t' equal to the time remaining after two transfers.
        threshold = max(2*transfer, (2*cost-2*transfer*mem)/(qpu-mem))
        examples[str(r)] = dict(earliest_memory_idle_s=threshold, transfer=st)
    return examples


def enumerate_grid_ports(k):
    """Bound for a stated variant with a point port and Manhattan unit hops."""
    return sum(abs(x)+abs(y)<=k for x in range(-k,k+1) for y in range(-k,k+1))
