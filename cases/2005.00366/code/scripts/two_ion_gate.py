"""Construct a robust shared drive using exact segmented integrals."""

import json
from pathlib import Path

import numpy as np
from scipy.constants import atomic_mass, hbar
from scipy.linalg import eigh, null_space


def two_ion_modes(config):
    """Two transverse axes, with the in-phase and out-of-phase modes on each."""
    mass = config["ion_mass_amu"] * atomic_mass
    axial = config["axial_com_hz"]
    com = np.asarray(config["transverse_com_hz"])
    frequencies = np.column_stack((com, np.sqrt(com ** 2 - axial ** 2))).ravel()
    k = 2 * np.pi / config["wavelength_m"]
    zero_point = np.sqrt(hbar / (4 * np.pi * mass * frequencies))
    eta = k * zero_point[None, :] * (
        np.array([[1, 1, 1, 1], [1, -1, 1, -1]]) / np.sqrt(2))
    return frequencies, eta


def segment_integrals(theta, count):
    """Zeroth/first moments and imaginary ordered integral in time/T units."""
    width = 1.0 / count
    center = (np.arange(count) + 0.5) * width
    half_angle = 0.5 * theta * width
    angle = 2 * half_angle
    sinc = np.sinc(half_angle / np.pi)
    if abs(half_angle) < 1e-3:
        dsinc = -half_angle / 3 + half_angle ** 3 / 30 - half_angle ** 5 / 840
        diagonal = width ** 2 * (angle / 6 - angle ** 3 / 120 + angle ** 5 / 5040)
    else:
        dsinc = (half_angle * np.cos(half_angle) - np.sin(half_angle)) / half_angle ** 2
        diagonal = width ** 2 * (angle - np.sin(angle)) / angle ** 2
    rotation = np.exp(1j * theta * center)
    zeroth = width * rotation * sinc
    first = center * zeroth - 0.5j * width ** 2 * rotation * dsinc
    return zeroth, first, diagonal


def matrices(theta, eta, basis):
    """Real quadratic phase form and constraints in the Fourier coefficients."""
    dimension = basis.shape[1]
    phase_form = np.zeros((dimension, dimension))
    constraints = []
    for detuning, eta_product in zip(theta, eta[0] * eta[1]):
        zeroth, first, diagonal = segment_integrals(detuning, len(basis))
        weighted = zeroth[:, None] * basis
        prefix = np.cumsum(weighted, axis=0) - weighted
        ordered = np.einsum("sa,sb->ab", weighted, prefix.conj())
        ordered += 1j * diagonal * np.einsum("sa,sb->ab", basis, basis.conj())
        phase_form += 0.5 * eta_product * ordered.imag
        center = np.exp(-0.5j * detuning)
        constraints.append((center * np.einsum("s,sa->a", zeroth, basis)).real)
        constraints.append((center * np.einsum("s,sa->a", first - 0.5 * zeroth, basis)).imag)
    return 0.5 * (phase_form + phase_form.T), np.asarray(constraints)


def observe(drive, theta, eta):
    phase, displacement, moment = 0.0, [], []
    for p, detuning in enumerate(theta):
        zeroth, first, diagonal = segment_integrals(detuning, len(drive))
        areas = zeroth * drive
        prefix = np.cumsum(areas) - areas
        phase += 0.5 * eta[0, p] * eta[1, p] * (
            np.sum(areas * prefix.conj()).imag + diagonal * np.sum(abs(drive) ** 2))
        displacement.append(0.5 * np.sum(areas))
        moment.append(0.5 * np.sum(first * drive))
    return phase, np.asarray(displacement) * eta, np.asarray(moment) * eta


def control_limits(drive, duration):
    frequency = np.abs(drive) / (2 * np.pi * duration)
    steps = np.angle(drive[1:] * drive[:-1].conj())
    return dict(maximum_rabi_hz=float(frequency.max()),
                maximum_step_rabi_hz=float(np.max(np.abs(np.diff(frequency)))),
                maximum_step_phase_rad=float(np.max(np.abs(steps))))


def construct(config):
    frequencies, eta = two_ion_modes(config)
    duration = config["duration_s"]
    theta = 2 * np.pi * duration * (frequencies - config["laser_detuning_hz"])
    target = np.pi * config["target_phase_over_pi"]
    count = config["segments"]
    time = (np.arange(count) + 0.5) / count
    candidates = []
    for order in config["fourier_orders"]:
        basis = np.sin(np.pi * time[:, None]) ** 2 * np.exp(
            2j * np.pi * (time[:, None] - 0.5) * np.arange(-order, order + 1))
        phase_form, constraint = matrices(theta, eta, basis)
        free = null_space(constraint, rcond=1e-11)
        if free.shape[1] == 0:
            continue
        norm = np.einsum("sa,sb->ab", basis.conj(), basis).real / count
        reduced_phase = np.einsum("ia,ij,jb->ab", free, phase_form, free)
        reduced_norm = np.einsum("ia,ij,jb->ab", free, norm, free)
        score, vectors = eigh(reduced_phase, reduced_norm)
        if score[-1] <= 0:
            continue
        coefficients = np.einsum("ia,a->i", free, vectors[:, -1])
        drive = np.einsum("si,i->s", basis, coefficients) * np.sqrt(target / score[-1])
        limits = control_limits(drive, duration)
        phase, displacement, moment = observe(drive, theta, eta)
        within = (limits["maximum_rabi_hz"] <= config["maximum_rabi_hz"]
                  and limits["maximum_step_rabi_hz"] <= config["maximum_step_rabi_hz"]
                  and limits["maximum_step_phase_rad"] <= np.pi * config["maximum_step_phase_over_pi"])
        row = dict(order=order, phase=float(phase), **limits, within_bounds=bool(within),
                   max_displacement=float(np.max(abs(displacement))),
                   max_first_moment=float(np.max(abs(moment))),
                   drive=drive)
        candidates.append(row)
    selected = min((x for x in candidates if x["within_bounds"]),
                   key=lambda x: x["maximum_rabi_hz"], default=None)
    if selected is None:
        selected = min(candidates, key=lambda x: x["maximum_rabi_hz"])
    metadata = dict(
        selected_order=selected["order"], mode_frequencies_hz=frequencies.tolist(),
        lamb_dicke=eta.tolist(), relative_detuning_hz=(theta / (2 * np.pi * duration)).tolist(),
        candidates=[{k: v for k, v in row.items() if k != "drive"} for row in candidates],
    )
    return selected["drive"], metadata


def main():
    config = json.loads(Path("config/two-ion.json").read_text())
    drive, metadata = construct(config)
    Path("results/two-ion-summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    np.savetxt("results/two-ion-pulse.csv", np.column_stack((drive.real, drive.imag)),
               delimiter=",", header="real_Omega_times_T,imag_Omega_times_T", comments="")
    row = next(x for x in metadata["candidates"] if x["order"] == metadata["selected_order"])
    print(json.dumps(row))


if __name__ == "__main__":
    main()
