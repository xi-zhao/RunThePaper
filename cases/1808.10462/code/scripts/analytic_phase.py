"""Independent piecewise-exact solution of the analytic Milne phase sequences."""
import json
from pathlib import Path

import numpy as np
from scipy.constants import atomic_mass, hbar


def concatenate(detuning_hz, duration):
    rotation = np.ones(1, complex)
    width = duration / 2**len(detuning_hz)
    for f in detuning_hz:
        rotation = np.r_[rotation, -np.exp(2j * np.pi * f * len(rotation) * width) * rotation]
    return rotation


def response(detuning_hz, duration, rotation):
    """Return alpha/(Omega T) and the signed area integral divided by (Omega T)^2."""
    theta = -2 * np.pi * duration * np.asarray(detuning_hz)
    width = 1 / len(rotation)
    center = (np.arange(len(rotation)) + 0.5) * width
    step = theta * width
    part = width * np.sinc(step[:, None] / (2 * np.pi)) * np.exp(1j * theta[:, None] * center) * rotation
    total = np.cumsum(part, axis=1)
    prior = np.pad(total[:, :-1], ((0, 0), (1, 0)))
    triangle = np.empty_like(step)
    small = abs(step) < 1e-3
    z = step[small]
    triangle[small] = width**2 * (z / 6 - z**3 / 120 + z**5 / 5040)
    z = step[~small]
    triangle[~small] = width**2 * (z - np.sin(z)) / z**2
    area = (part * prior.conj()).imag.sum(axis=1) + triangle * np.sum(abs(rotation)**2)
    return total[:, -1], area


def path(detuning_hz, duration, rotation, subdivisions=16):
    theta = -2 * np.pi * duration * detuning_hz
    count = len(rotation)
    times = np.linspace(0, 1, count * subdivisions + 1)
    centers = (times[1:] + times[:-1]) / 2
    width = 1 / (count * subdivisions)
    increment = np.repeat(rotation, subdivisions) * np.exp(1j * theta * centers) * width * np.sinc(theta * width / (2 * np.pi))
    return np.r_[0j, np.cumsum(increment)]


def coupling(config, frequencies, parity):
    # A common -i on each mode leaves both the displacement norms and the area invariant.
    zpf = np.sqrt(hbar / (4 * np.pi * config["mass_amu"] * atomic_mass * np.asarray(frequencies)))
    one = 0.5 * (2 * np.pi / config["projected_wavelength_m"]) * zpf / np.sqrt(2)
    return np.array([one, one * np.asarray(parity)])


def scaled_gate(config, detunings, duration, rotation, f):
    displacement, area = response(detunings, duration, rotation)
    angle = 2 * np.sum(f[0] * f[1] * area)
    assert abs(angle) > 1e-12
    omega_t = np.sqrt(np.pi / 4 / abs(angle))
    return float(omega_t / (2 * np.pi * duration)), f * displacement * omega_t, float(np.copysign(np.pi / 4, angle))


def observables(displacement, angle, nbar):
    thermal = np.asarray(nbar) + 0.5
    plus, minus = (displacement[0] + displacement[1], displacement[0] - displacement[1])
    exponents = -4 * np.array([np.sum(abs(x)**2 * thermal) for x in (plus, minus, displacement[0])])
    ep, em, single = np.exp(exponents)
    p1 = -np.expm1(exponents[:2]).sum() / 4
    p0 = (2 + ep + em + 4 * np.cos(2 * angle) * single) / 8
    p2 = (2 + ep + em - 4 * np.cos(2 * angle) * single) / 8
    bell = (2 + ep + em + abs(ep - em - 4j * single * np.sin(2 * angle))) / 8
    return [float(x) for x in (p0, p1, p2, bell)]


def complex_list(z):
    return np.stack((np.real(z), np.imag(z)), axis=-1).tolist()


def single_ion(config):
    c = config["figure2b"]
    t = c["duration_s"]
    d = c["drive_from_mode1_hz"] + np.array([0, c["mode1_minus_mode2_hz"]])
    seq = concatenate(d, t)
    primitive = np.ones(1)
    res, _ = response(d, t, seq)
    compare, _ = response(d, t, primitive)
    phase = np.mod(-np.angle(seq) / np.pi, 2)
    return dict(detunings_hz=d.tolist(), phases_over_pi=phase.tolist(),
        max_printed_phase_difference=float(abs(phase-c["paper_phase_over_pi"]).max()),
        pm_endpoints=complex_list(res), primitive_endpoints=complex_list(compare),
        pm_paths=[complex_list(path(det,t,seq)) for det in d],
        primitive_paths=[complex_list(path(det,t,primitive)) for det in d])


def fidelity_sweep(config):
    c = config["figure3"]
    t = c["cycles_across_gap"] / c["gap_hz"]
    f = coupling(config,[c["y_com_hz"]+c["gap_hz"],c["y_com_hz"]],[-1,1])
    rows = []
    for x in np.linspace(-1,0,c["grid_points"]):
        d = c["gap_hz"] * np.array([x,x+1])
        rotation = concatenate(d[::-1] if x >= -0.5 else d,t)
        entry = {"fraction":float(x)}
        for name,pulse in (("unmodulated",np.ones(1)),("phase_modulated",rotation)):
            rabi, displacement, angle = scaled_gate(config,d,t,pulse,f)
            entry[name] = dict(rabi_hz=rabi,angle_rad=angle,max_displacement=float(abs(displacement).max()),
                              observables=[observables(displacement,angle,n) for n in c["mean_occupations"]])
        rows.append(entry)
    return dict(duration_s=t,rows=rows)


def static_scan(config):
    c = config["figure4"]
    t = c["duration_s"]
    fx, fy = c["transverse_com_hz"]
    axial = c["axial_com_hz"]
    freqs = np.array([fx,np.sqrt(fx**2-axial**2),fy,np.sqrt(fy**2-axial**2)])
    assert np.all(np.diff(freqs) < 0)
    detunings = freqs[-1]+c["drive_from_mode4_hz"]-freqs
    f = coupling(config,freqs,[1,-1,1,-1])
    seqs = {"unmodulated":np.ones(1), "second_order":concatenate([detunings[3]]*2,t),
            "third_order":concatenate([detunings[1],detunings[2],*([detunings[3]]*3)],t)}
    offsets = np.linspace(*c["scan_hz"],c["scan_points"])
    fits = np.array(c["order_fit_offset_hz"])
    stats = {}
    for name,rotation in seqs.items():
        rabi, _, angle = scaled_gate(config,detunings,t,rotation,f)
        scale = 2*np.pi*rabi*t
        occupation = [0,0,0,c["mode4_mean_occupation"]]
        r = []
        for shift in offsets:
            alpha,area=response(detunings+shift,t,rotation)
            phase=2*np.sum(f[0]*f[1]*area)*scale**2
            r.append(dict(shift_hz=float(shift),mode4_power=float(abs(alpha[-1])**2),
                          p1=observables(f*alpha*scale,phase,occupation)[1]))
        power = np.array([abs(response([detunings[-1]+x],t,rotation)[0][0])**2 for x in fits])
        exponent = np.polyfit(np.log(fits),np.log(power),1)[0]
        stats[name] = dict(segments=len(rotation),rabi_hz=rabi,nominal_pair_phase_rad=angle,
            mode4_power_exponent=float(exponent),fit_mode4_power=power.tolist(),rows=r,
            mode4_path_plus_500_hz=complex_list(path(detunings[-1]+c["motion_plot_offset_hz"],t,rotation)))
    return dict(mode_frequencies_hz=freqs.tolist(),nominal_detunings_hz=detunings.tolist(),results=stats)


def main():
    cfg=json.loads(Path("config/analytic-phase.json").read_text())
    result=dict(figure2b=single_ion(cfg),figure3=fidelity_sweep(cfg),figure4=static_scan(cfg))
    Path("results/analytic-phase.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    main()
