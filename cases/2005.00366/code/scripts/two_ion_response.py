"""Independent four-control comparison under the target paper's Fig. 3 settings."""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[key] = "1"
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, null_space
from two_ion_gate import two_ion_modes, matrices, segment_integrals, observe, control_limits


def thermal_error(phase_error, displacement, occupation):
    """The source's thermal-trace operational metric, not channel average fidelity."""
    signs = np.array([[1, 1], [1, -1], [-1, 1], [-1, -1]])
    d = np.einsum("ij,jp->ip", signs, displacement)
    decay = (occupation + 0.5) * np.sum(abs(d) ** 2, axis=1)
    angle = phase_error * signs.prod(axis=1)
    loss = np.mean(-np.expm1(-decay) + np.exp(-decay) * 2 * np.sin(angle / 2) ** 2)
    imaginary = np.mean(np.exp(-decay) * np.sin(angle))
    return float(2 * loss - loss ** 2 - imaginary ** 2)


def build_control(config, robust, bounded):
    f, eta = two_ion_modes(config)
    count, duration = config["segments"], config["duration_s"]
    theta = 2 * np.pi * duration * (f - config["laser_detuning_hz"])
    time = (np.arange(count) + 0.5) / count
    target = np.pi * config["target_phase_over_pi"]
    candidates = []
    orders = config["fourier_orders"] if bounded else [None]
    for order in orders:
        if bounded:
            basis = np.sin(np.pi * time[:, None]) ** 2 * np.exp(
                2j * np.pi * (time[:, None] - 0.5) * np.arange(-order, order + 1))
        else:
            half = np.eye(count, count // 2)
            basis = np.column_stack((half + half[::-1], 1j * (half - half[::-1])))
        phase_form, constraint = matrices(theta, eta, basis)
        if not robust:
            constraint = constraint[::2]
        free = null_space(constraint, rcond=1e-11)
        if not free.shape[1]:
            continue
        norm = np.einsum("sa,sb->ab", basis.conj(), basis).real / count
        h = np.einsum("ia,ib->ab", free, np.einsum("ij,jb->ib", phase_form, free))
        g = np.einsum("ia,ib->ab", free, np.einsum("ij,jb->ib", norm, free))
        eig, vec = eigh(h, g, subset_by_index=[len(h) - 1, len(h) - 1])
        if eig[0] <= 0:
            continue
        coeff = np.einsum("ia,a->i", free, vec[:, 0])
        u = np.einsum("si,i->s", basis, coeff) * np.sqrt(target / eig[0])
        limits = control_limits(u, duration)
        eligible = limits["maximum_rabi_hz"] <= config["maximum_rabi_hz"]
        if bounded:
            eligible = eligible and limits["maximum_step_rabi_hz"] <= config["maximum_step_rabi_hz"]
            eligible = eligible and limits["maximum_step_phase_rad"] <= np.pi * config["maximum_step_phase_over_pi"]
        phase, displacement, moment = observe(u, theta, eta)
        row = dict(order=order, eligible=bool(eligible), phase_rad=float(phase),
                   max_displacement=float(abs(displacement).max()),
                   max_first_moment=float(abs(moment).max()), **limits,
                   mean_power=float(np.mean(abs(u) ** 2)))
        candidates.append((row, u))
    eligible = [(r, u) for r, u in candidates if r["eligible"]]
    if not eligible:
        raise ValueError("No candidate satisfies the declared control limits")
    row, u = min(eligible, key=lambda item: item[0]["maximum_rabi_hz"])
    return u, dict(selected=row, candidates=[r for r, _ in candidates])


def filters(u, theta, eta, duration, frequencies):
    """Bilateral responses in s^2 per squared angular-frequency amplitude."""
    t_weighted = np.zeros((2, len(frequencies)))
    integrated = np.zeros_like(t_weighted)
    for p, detuning in enumerate(theta):
        base = np.sum(segment_integrals(detuning, len(u))[0] * u)
        coupling = np.sum(eta[:, p] ** 2) / 4
        for j, sign in enumerate((1, -1)):
            for k, frequency in enumerate(frequencies):
                omega = sign * 2 * np.pi * frequency * duration
                zeroth, first, _ = segment_integrals(detuning + omega, len(u))
                t_weighted[j, k] += coupling * duration ** 2 * abs(np.sum(first * u)) ** 2
                integral = (np.sum(zeroth * u) - base) / (1j * omega)
                integrated[j, k] += coupling * duration ** 2 * abs(integral) ** 2
    return t_weighted, integrated


def main():
    spec = json.loads(Path("config/two-ion-response.json").read_text())
    config = json.loads(Path(spec["base_config"]).read_text())
    f, eta = two_ion_modes(config)
    duration = config["duration_s"]
    theta = (f - config["laser_detuning_hz"]) * 2 * np.pi * duration
    target = np.pi * config["target_phase_over_pi"]
    frequency = np.geomspace(spec["frequency_hz"]["minimum"], spec["frequency_hz"]["maximum"], spec["frequency_hz"]["count"])
    ds = spec["detuning_shift_hz"]
    shifts = np.linspace(ds["minimum"], ds["maximum"], ds["count"])
    arrays = dict(frequency_hz=frequency, laser_shift_hz=shifts, mode_frequencies_hz=f, lamb_dicke=eta)
    summary = dict(conditions=spec, cases={})
    for case in spec["cases"]:
        u, meta = build_control(config, case.startswith("robust"), case.endswith("_bounded"))
        arrays[case + "_drive"] = u
        phases, displacements, errors, phase_losses, motion_losses = [], [], [], [], []
        for shift in shifts:
            phase, displacement, _ = observe(u, theta - shift * 2 * np.pi * duration, eta)
            phases.append(phase - target)
            displacements.append(displacement)
            errors.append([thermal_error(phase-target, displacement, n) for n in spec["occupations"]])
            phase_losses.append(float(np.sin(phase - target) ** 2))
            motion_losses.append([thermal_error(0, displacement, n) for n in spec["occupations"]])
        arrays[case + "_phase_error"] = np.asarray(phases)
        arrays[case + "_displacement"] = np.asarray(displacements)
        arrays[case + "_infidelity"] = np.asarray(errors)
        arrays[case + "_phase_loss"] = np.asarray(phase_losses)
        arrays[case + "_motion_loss"] = np.asarray(motion_losses)
        prescribed, physical = filters(u, theta, eta, duration, frequency)
        arrays[case + "_source_filter_s2"] = prescribed
        arrays[case + "_integrated_filter_s2"] = physical
        fit = (frequency >= spec["validation"]["low_frequency_fit_hz"][0]) & (frequency <= spec["validation"]["low_frequency_fit_hz"][1])
        meta["low_frequency_source_filter_power"] = float(np.polyfit(np.log(frequency[fit]), np.log(prescribed.mean(axis=0)[fit]), 1)[0])
        meta["low_frequency_integrated_filter_power"] = float(np.polyfit(np.log(frequency[fit]), np.log(physical.mean(axis=0)[fit]), 1)[0])
        stat = []
        for shift in spec["validation"]["small_static_shift_hz"]:
            for sign in (-1, 1):
                phase, disp, _ = observe(u, theta - sign * shift * 2 * np.pi * duration, eta)
                stat.append(dict(shift_hz=sign * shift, displacement_norm=float(np.linalg.norm(disp)),
                                 phase_error=float(phase-target), total_infidelity=thermal_error(phase-target, disp, 0),
                                 motion_infidelity=thermal_error(0, disp, 0)))
        meta["small_static_scan"] = stat
        sx = np.asarray(spec["validation"]["small_static_shift_hz"])
        for key in ("displacement_norm", "total_infidelity", "motion_infidelity"):
            sy = [np.mean([r[key] for r in stat if abs(r["shift_hz"]) == x]) for x in sx]
            meta[key + "_small_shift_power"] = float(np.polyfit(np.log(sx), np.log(sy), 1)[0])
        summary["cases"][case] = meta
        print(json.dumps({"case": case, **meta["selected"],
                          "filter_power": meta["low_frequency_source_filter_power"],
                          "total_error_power": meta["total_infidelity_small_shift_power"]}), flush=True)
    for key, value in arrays.items():
        assert np.isfinite(value).all(), key
    Path("results").mkdir(exist_ok=True)
    np.savez_compressed("results/two-ion-response.npz", **arrays)
    Path("results/two-ion-response-summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
