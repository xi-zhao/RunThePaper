"""Fail-closed reanalysis channel for unpublished experimental arrays."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from .metrology import hom_delay_curve
from .quantum import FOCK_LABELS, output_probabilities, spectrum_weighted_hom_visibility


@dataclass(frozen=True)
class RequiredInput:
    filename: str
    columns: tuple[str, ...]
    purpose: str


REQUIRED_INPUTS = (
    RequiredInput(
        "fig1d_shg.csv",
        ("source", "wavelength_nm", "shg_power", "sigma"),
        "the two measured SHG spectra in Main Fig. 1(d)",
    ),
    RequiredInput(
        "fig2_mzi.csv",
        ("input_port", "output_port", "theta_rad", "power", "sigma"),
        "the four classical MZI transfer scans in Main Fig. 2",
    ),
    RequiredInput(
        "fig3_quantum.csv",
        ("state", "theta_rad", "phi_rad", "coincidence_hz", "sigma_hz"),
        "the six quantum-interference surfaces and cuts in Main Fig. 3",
    ),
    RequiredInput(
        "fig4_hom.csv",
        ("delay_fs", "coincidence_hz", "sigma_hz"),
        "the off-chip HOM delay scan in Main Fig. 4(b)",
    ),
    RequiredInput(
        "supp_s4_car.csv",
        ("source", "delay_ns", "coincidence_count"),
        "the source-resolved CAR histograms in Supplement Fig. S4",
    ),
    RequiredInput(
        "supp_s5_reflectivity.csv",
        ("device", "wavelength_nm", "reflectivity", "sigma"),
        "the LNOI and fiber reflectivity spectra in Supplement Fig. S5(a)",
    ),
    RequiredInput(
        "supp_s5_grating.csv",
        ("wavelength_nm", "efficiency_db", "sigma_db"),
        "the grating response in Supplement Fig. S5(d)",
    ),
    RequiredInput(
        "supp_s6_coupler.csv",
        ("output", "coupler_count", "relative_power", "sigma"),
        "the directional-coupler loss points in Supplement Fig. S6",
    ),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_inputs(root: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for requirement in REQUIRED_INPUTS:
        path = root / requirement.filename
        row: dict[str, object] = {
            "filename": requirement.filename,
            "purpose": requirement.purpose,
            "required_columns": list(requirement.columns),
            "present": path.is_file(),
        }
        if path.is_file():
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                actual = tuple(reader.fieldnames or ())
            row.update(
                {
                    "actual_columns": list(actual),
                    "schema_valid": actual == requirement.columns,
                    "sha256": sha256_file(path),
                }
            )
        rows.append(row)
    ready = all(row["present"] and row.get("schema_valid") for row in rows)
    return {"status": "ready" if ready else "blocked_missing_inputs", "inputs": rows}


def _numeric_rows(root: Path, requirement: RequiredInput) -> list[dict[str, str]]:
    path = root / requirement.filename
    if not path.is_file():
        raise FileNotFoundError(f"required author data missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != requirement.columns:
            raise ValueError(f"schema mismatch: {path}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"empty author data: {path}")
    return rows


def _weighted_linear(
    design: np.ndarray, values: np.ndarray, sigma: np.ndarray
) -> dict[str, object]:
    weights = 1.0 / np.asarray(sigma, dtype=float) ** 2
    design = np.asarray(design, dtype=float)
    values = np.asarray(values, dtype=float)
    normal = design.T @ (weights[:, None] * design)
    covariance = np.linalg.inv(normal)
    coefficients = covariance @ (design.T @ (weights * values))
    residual = (values - design @ coefficients) / sigma
    return {
        "coefficients": coefficients.tolist(),
        "covariance": covariance.tolist(),
        "chi2": float(residual @ residual),
        "dof": int(values.size - coefficients.size),
    }


def reanalyse_available_inputs(root: Path) -> dict[str, object]:
    """Reanalyse all measurements, refusing any incomplete input set."""

    inventory = inspect_inputs(root)
    if inventory["status"] != "ready":
        raise FileNotFoundError(
            "experimental reanalysis is blocked by missing author arrays"
        )

    shg_rows = _numeric_rows(root, REQUIRED_INPUTS[0])
    shg_peaks: dict[str, float] = {}
    for source in sorted({row["source"] for row in shg_rows}):
        subset = [row for row in shg_rows if row["source"] == source]
        peak = max(subset, key=lambda row: float(row["shg_power"]))
        shg_peaks[source] = float(peak["wavelength_nm"])

    mzi_rows = _numeric_rows(root, REQUIRED_INPUTS[1])
    mzi_fits: dict[str, object] = {}
    for key in sorted({(row["input_port"], row["output_port"]) for row in mzi_rows}):
        subset = [
            row for row in mzi_rows if (row["input_port"], row["output_port"]) == key
        ]
        theta = np.asarray([float(row["theta_rad"]) for row in subset])
        design = np.column_stack((np.ones(theta.size), np.cos(theta), np.sin(theta)))
        mzi_fits[f"{key[0]}->{key[1]}"] = _weighted_linear(
            design,
            np.asarray([float(row["power"]) for row in subset]),
            np.asarray([float(row["sigma"]) for row in subset]),
        )

    quantum_rows = _numeric_rows(root, REQUIRED_INPUTS[2])
    model_values: list[float] = []
    observations: list[float] = []
    uncertainties: list[float] = []
    for row in quantum_rows:
        if row["state"] not in FOCK_LABELS:
            raise ValueError(f"unknown Fock state {row['state']}")
        model_values.append(
            float(
                output_probabilities(float(row["theta_rad"]), float(row["phi_rad"]))[
                    FOCK_LABELS.index(row["state"])
                ]
            )
        )
        observations.append(float(row["coincidence_hz"]))
        uncertainties.append(float(row["sigma_hz"]))
    quantum_fit = _weighted_linear(
        np.column_stack((np.ones(len(model_values)), model_values)),
        np.asarray(observations),
        np.asarray(uncertainties),
    )

    hom_rows = _numeric_rows(root, REQUIRED_INPUTS[3])
    delay = np.asarray([float(row["delay_fs"]) for row in hom_rows])
    counts = np.asarray([float(row["coincidence_hz"]) for row in hom_rows])
    sigma = np.asarray([float(row["sigma_hz"]) for row in hom_rows])
    parameters, covariance = curve_fit(
        lambda x, baseline, visibility, width: hom_delay_curve(
            x, baseline_hz=baseline, visibility=visibility, fwhm_fs=width
        ),
        delay,
        counts,
        sigma=sigma,
        absolute_sigma=True,
        p0=(float(np.max(counts)), 0.83, 72.0),
        bounds=((0.0, 0.0, 1e-6), (np.inf, 1.0, np.inf)),
    )

    car_rows = _numeric_rows(root, REQUIRED_INPUTS[4])
    car: dict[str, float] = {}
    for source in sorted({row["source"] for row in car_rows}):
        subset = [row for row in car_rows if row["source"] == source]
        central = [
            float(row["coincidence_count"])
            for row in subset
            if abs(float(row["delay_ns"])) <= 0.5
        ]
        background = [
            float(row["coincidence_count"])
            for row in subset
            if abs(float(row["delay_ns"])) >= 5.0
        ]
        if len(central) != 1 or not background:
            raise ValueError("CAR data must have one central bin and background bins")
        car[source] = central[0] / float(np.mean(background))

    reflectivity_rows = _numeric_rows(root, REQUIRED_INPUTS[5])
    grating_rows = _numeric_rows(root, REQUIRED_INPUTS[6])
    wavelength = np.asarray(
        sorted({float(row["wavelength_nm"]) for row in reflectivity_rows})
    )
    grating_x = np.asarray([float(row["wavelength_nm"]) for row in grating_rows])
    grating_t = 10.0 ** (
        np.asarray([float(row["efficiency_db"]) for row in grating_rows]) / 10.0
    )
    spectral_visibility: dict[str, float] = {}
    for device in sorted({row["device"] for row in reflectivity_rows}):
        subset = [row for row in reflectivity_rows if row["device"] == device]
        x = np.asarray([float(row["wavelength_nm"]) for row in subset])
        r = np.asarray([float(row["reflectivity"]) for row in subset])
        order = np.argsort(x)
        x, r = x[order], r[order]
        signal_r = np.interp(wavelength, x, r)
        idler_wavelength = 1.0 / (1.0 / 781.0 - 1.0 / wavelength)
        idler_r = np.interp(idler_wavelength, x, r)
        weights = np.interp(wavelength, grating_x, grating_t) * np.interp(
            idler_wavelength, grating_x, grating_t
        )
        spectral_visibility[device] = spectrum_weighted_hom_visibility(
            signal_r, idler_r, weights
        )

    coupler_rows = _numeric_rows(root, REQUIRED_INPUTS[7])
    counts = np.asarray([float(row["coupler_count"]) for row in coupler_rows])
    loss_db = -10.0 * np.log10(
        np.asarray([float(row["relative_power"]) for row in coupler_rows])
    )
    coupler_fit = np.polyfit(counts, loss_db, deg=1).tolist()

    return {
        "inventory": inventory,
        "shg_peak_wavelength_nm": shg_peaks,
        "mzi_fits": mzi_fits,
        "quantum_probability_fit": quantum_fit,
        "hom_fit": {
            "baseline_hz": float(parameters[0]),
            "visibility": float(parameters[1]),
            "fwhm_fs": float(parameters[2]),
            "covariance": covariance.tolist(),
        },
        "car": car,
        "spectral_visibility": spectral_visibility,
        "coupler_loss_linear_fit": coupler_fit,
    }
