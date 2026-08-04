"""Independent two-qubit numerics for arXiv:2606.30255.

The generated theory lane evaluates Born probabilities through explicit
4-by-4 density-matrix traces.  A separately implemented scalar contraction is
kept only as an analytic scientific check.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import Callable

import numpy as np


PAPER_ID = "2606.30255"
SYMMETRIC_LIMIT = -1.0 / 8.0
ASYMMETRIC_LIMIT = (1.0 - sqrt(3.0)) / 4.0
ANGLE_START_DEG = 0.0
ANGLE_STOP_DEG = 360.0
ANGLE_STEP_DEG = 0.25


@dataclass(frozen=True)
class TargetSpec:
    target_id: str
    slug: str
    figure_id: str
    scan_kind: str
    w: float
    v: float
    xi_rad: float
    spacing_deg: float | None
    alice_origin_deg: float | None
    bob_origin_deg: float | None
    x_label: str
    y_range: tuple[float, float]
    violation_limit: float
    reported_fidelity: float
    source_figure_pdf: str

    def origins_and_spacing(self, scan_angle_deg: float) -> tuple[float, float, float]:
        """Return Alice origin, Bob origin, and three-setting spacing."""

        if self.scan_kind == "relative_spacing":
            return (
                _required(self.alice_origin_deg, "alice_origin_deg"),
                _required(self.bob_origin_deg, "bob_origin_deg"),
                scan_angle_deg,
            )
        if self.scan_kind == "common_origin":
            return (
                scan_angle_deg,
                scan_angle_deg,
                _required(self.spacing_deg, "spacing_deg"),
            )
        if self.scan_kind == "bob_origin":
            return (
                _required(self.alice_origin_deg, "alice_origin_deg"),
                scan_angle_deg,
                _required(self.spacing_deg, "spacing_deg"),
            )
        if self.scan_kind == "alice_origin":
            return (
                scan_angle_deg,
                _required(self.bob_origin_deg, "bob_origin_deg"),
                _required(self.spacing_deg, "spacing_deg"),
            )
        raise ValueError(f"unsupported scan kind: {self.scan_kind}")


TARGET_SPECS: dict[str, TargetSpec] = {
    "T-FIG003": TargetSpec(
        target_id="T-FIG003",
        slug="fig003_theory",
        figure_id="FIG003",
        scan_kind="relative_spacing",
        w=0.50,
        v=0.98,
        xi_rad=pi,
        spacing_deg=None,
        alice_origin_deg=0.0,
        bob_origin_deg=0.0,
        x_label=r"$\phi (^\circ)$",
        y_range=(-0.18, 1.05),
        violation_limit=SYMMETRIC_LIMIT,
        reported_fidelity=0.985,
        source_figure_pdf="tequila_hat_paper_leastsquare.pdf",
    ),
    "T-FIG004": TargetSpec(
        target_id="T-FIG004",
        slug="fig004_theory",
        figure_id="FIG004",
        scan_kind="common_origin",
        w=0.36,
        v=0.99,
        xi_rad=pi,
        spacing_deg=30.0,
        alice_origin_deg=None,
        bob_origin_deg=None,
        x_label=r"$\Theta (^\circ)$",
        y_range=(-0.16, 0.53),
        violation_limit=SYMMETRIC_LIMIT,
        reported_fidelity=0.978,
        source_figure_pdf="both_move_paper_leastsquare.pdf",
    ),
    "T-FIG005A": TargetSpec(
        target_id="T-FIG005A",
        slug="fig005a_theory",
        figure_id="FIG005A",
        scan_kind="bob_origin",
        w=0.35,
        v=0.89,
        xi_rad=pi,
        spacing_deg=30.0,
        alice_origin_deg=0.0,
        bob_origin_deg=None,
        x_label=r"$\Theta_{\mathrm{Bob}} (^\circ)$",
        y_range=(-0.23, 0.84),
        violation_limit=ASYMMETRIC_LIMIT,
        reported_fidelity=0.896,
        source_figure_pdf="A_fixed_paper_leastsquare.pdf",
    ),
    "T-FIG005B": TargetSpec(
        target_id="T-FIG005B",
        slug="fig005b_theory",
        figure_id="FIG005B",
        scan_kind="alice_origin",
        w=0.41,
        v=0.90,
        xi_rad=pi,
        spacing_deg=30.0,
        alice_origin_deg=None,
        bob_origin_deg=0.0,
        x_label=r"$\Theta_{\mathrm{Alice}} (^\circ)$",
        y_range=(-0.23, 0.65),
        violation_limit=ASYMMETRIC_LIMIT,
        reported_fidelity=0.914,
        source_figure_pdf="B_fixed_paper_leastsquare.pdf",
    ),
}


def _required(value: float | None, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required for this target")
    return value


def measurement_state(angle_deg: float) -> np.ndarray:
    """Paper Eq. (7) in the ordered basis (H, V)."""

    angle_rad = np.deg2rad(angle_deg)
    return np.array([np.sin(angle_rad), np.cos(angle_rad)], dtype=np.complex128)


def projector(angle_deg: float) -> np.ndarray:
    state = measurement_state(angle_deg)
    return np.outer(state, state.conj())


def density_matrix(w: float, v: float, xi_rad: float = pi) -> np.ndarray:
    """Paper Eqs. (18) and (20) in the basis (HH, HV, VH, VV)."""

    if not 0.0 <= w <= 1.0:
        raise ValueError("w must lie in [0, 1]")
    if not 0.0 <= v <= 1.0:
        raise ValueError("v must lie in [0, 1]")
    psi = np.array(
        [0.0, sqrt(w), np.exp(1j * xi_rad) * sqrt(1.0 - w), 0.0],
        dtype=np.complex128,
    )
    return v * np.outer(psi, psi.conj()) + (1.0 - v) * np.eye(4) / 4.0


def born_probability_matrix(
    alice_angle_deg: float,
    bob_angle_deg: float,
    *,
    w: float,
    v: float,
    xi_rad: float = pi,
) -> float:
    """Generated numerical path: explicit density-matrix Born trace."""

    rho = density_matrix(w=w, v=v, xi_rad=xi_rad)
    joint_projector = np.kron(projector(alice_angle_deg), projector(bob_angle_deg))
    probability = np.trace(rho @ joint_projector)
    return float(np.real_if_close(probability, tol=1000).real)


def born_probability_analytic(
    alice_angle_deg: float,
    bob_angle_deg: float,
    *,
    w: float,
    v: float,
    xi_rad: float = pi,
) -> float:
    """Independent scalar contraction used only as an analytic check."""

    alice_rad = np.deg2rad(alice_angle_deg)
    bob_rad = np.deg2rad(bob_angle_deg)
    amplitude = (
        sqrt(w) * np.sin(alice_rad) * np.cos(bob_rad)
        + np.exp(1j * xi_rad)
        * sqrt(1.0 - w)
        * np.cos(alice_rad)
        * np.sin(bob_rad)
    )
    return float(v * abs(amplitude) ** 2 + (1.0 - v) / 4.0)


def three_setting_probabilities(
    alice_origin_deg: float,
    bob_origin_deg: float,
    spacing_deg: float,
    *,
    w: float,
    v: float,
    xi_rad: float = pi,
    probability_fn: Callable[..., float] = born_probability_matrix,
) -> dict[str, float]:
    """Evaluate the three probabilities and Wigner combination."""

    p_abprime = probability_fn(
        alice_origin_deg,
        bob_origin_deg + spacing_deg,
        w=w,
        v=v,
        xi_rad=xi_rad,
    )
    p_bcprime = probability_fn(
        alice_origin_deg + spacing_deg,
        bob_origin_deg + 2.0 * spacing_deg,
        w=w,
        v=v,
        xi_rad=xi_rad,
    )
    p_acprime = probability_fn(
        alice_origin_deg,
        bob_origin_deg + 2.0 * spacing_deg,
        w=w,
        v=v,
        xi_rad=xi_rad,
    )
    return {
        "p_abprime": p_abprime,
        "p_bcprime": p_bcprime,
        "p_acprime": p_acprime,
        "wigner": p_abprime + p_bcprime - p_acprime,
    }


def angle_grid() -> np.ndarray:
    count = int(round((ANGLE_STOP_DEG - ANGLE_START_DEG) / ANGLE_STEP_DEG)) + 1
    return np.linspace(ANGLE_START_DEG, ANGLE_STOP_DEG, count, dtype=float)


def evaluate_target(
    spec: TargetSpec,
    *,
    probability_fn: Callable[..., float] = born_probability_matrix,
) -> dict[str, np.ndarray]:
    angles = angle_grid()
    columns: dict[str, list[float]] = {
        "p_abprime": [],
        "p_bcprime": [],
        "p_acprime": [],
        "wigner": [],
    }
    for scan_angle_deg in angles:
        alice_origin, bob_origin, spacing = spec.origins_and_spacing(float(scan_angle_deg))
        values = three_setting_probabilities(
            alice_origin,
            bob_origin,
            spacing,
            w=spec.w,
            v=spec.v,
            xi_rad=spec.xi_rad,
            probability_fn=probability_fn,
        )
        for key in columns:
            columns[key].append(values[key])
    return {
        "angle_deg": angles,
        **{key: np.asarray(values, dtype=float) for key, values in columns.items()},
        "violation_limit": np.full_like(angles, spec.violation_limit, dtype=float),
    }


def singlet_fidelity(w: float, v: float) -> float:
    """F=<psi-|rho|psi-> for the paper's xi=pi state."""

    pure_overlap = 0.5 * (1.0 + 2.0 * sqrt(w * (1.0 - w)))
    return v * pure_overlap + (1.0 - v) / 4.0


def density_diagnostics(w: float, v: float, xi_rad: float = pi) -> dict[str, float]:
    rho = density_matrix(w=w, v=v, xi_rad=xi_rad)
    eigenvalues = np.linalg.eigvalsh(rho)
    return {
        "trace_error": float(abs(np.trace(rho) - 1.0)),
        "hermiticity_error": float(np.max(np.abs(rho - rho.conj().T))),
        "minimum_eigenvalue": float(np.min(eigenvalues)),
        "maximum_eigenvalue": float(np.max(eigenvalues)),
    }
