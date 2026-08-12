"""Scientific acceptance checks for the reconstructed model."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from .liouvillian import dense_propagate_final
from .model import ChannelRates, TransportModel, absorption_rate
from .observables import dephasing_rate_matrix, rescue_rate_matrix
from .simulation import PreparedTransport, ensemble_final_populations, prepare_ensemble


def _check(value: Any, passed: bool, tolerance: str, evidence: str) -> dict[str, Any]:
    return {
        "value": value,
        "passed": bool(passed),
        "tolerance": tolerance,
        "evidence": evidence,
    }


def run_scientific_checks() -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}

    sum_rule_errors: dict[str, float] = {}
    reverse_errors: dict[str, float] = {}
    dephasing_asymmetry: dict[str, float] = {}
    gamma = 0.73
    for n_sites in (3, 4, 8, 16, 32):
        clean = PreparedTransport.from_seed(
            TransportModel(n_sites, t_mean=0.0, delta_t=0.0), seed=0
        )
        p = clean.projectors
        rates = rescue_rate_matrix(p.cavity_weights, gamma)
        dark = p.dark_indices
        bright = p.bright_indices
        total_out = rates[np.ix_(bright, dark)].sum(axis=0)
        sum_rule_errors[str(n_sites)] = float(np.max(np.abs(total_out - gamma)))
        reverse_errors[str(n_sites)] = float(np.max(np.abs(rates[dark, :])))
        deph = dephasing_rate_matrix(p.eigenvectors, gamma_deph=0.41)
        dephasing_asymmetry[str(n_sites)] = float(np.max(np.abs(deph - deph.T)))

    max_sum_rule_error = max(sum_rule_errors.values())
    checks["photonic_sum_rule"] = _check(
        {"per_n_abs_error": sum_rule_errors, "max_abs_error": max_sum_rule_error},
        max_sum_rule_error < 1e-12,
        "max absolute error < 1e-12",
        "EQ004, ideal degenerate emitter manifold",
    )
    max_reverse = max(reverse_errors.values())
    checks["zero_dark_inflow"] = _check(
        {"per_n_max_rate": reverse_errors, "max_rate": max_reverse},
        max_reverse < 1e-12,
        "dark-destination rate < 1e-12",
        "EQ004, w_k=0 for every ideal dark destination",
    )
    max_asymmetry = max(dephasing_asymmetry.values())
    checks["dephasing_bidirectionality"] = _check(
        {"per_n_asymmetry": dephasing_asymmetry, "max_asymmetry": max_asymmetry},
        max_asymmetry < 1e-12,
        "max |W-W^T| < 1e-12",
        "rate equation following Main Eq. (4)",
    )

    detailed_balance_values = {
        str(x): absorption_rate(0.8, x) / 0.8 for x in (0.0, 0.1, 1.0, 10.0)
    }
    detailed_balance_error = max(
        abs(detailed_balance_values[str(x)] - (0.0 if x == 0 else np.exp(-1 / x)))
        for x in (0.0, 0.1, 1.0, 10.0)
    )
    checks["detailed_balance"] = _check(
        {"ratios": detailed_balance_values, "max_abs_error": detailed_balance_error},
        detailed_balance_error < 1e-15,
        "max absolute error < 1e-15",
        "EQ002 / SM Eq. (S17)",
    )

    small = PreparedTransport.from_seed(TransportModel(3), seed=11)
    rates = ChannelRates(gamma_rec=0.3, gamma_abs=0.07, gamma_deph=0.2, gamma_lead=0.5)
    sparse_rho = small.final_density(rates, 2.3)
    dense_rho = dense_propagate_final(small.generator(rates), small.rho0, 2.3)
    sparse_dense_error = float(np.max(np.abs(sparse_rho - dense_rho)))
    checks["sparse_dense_equivalence"] = _check(
        sparse_dense_error,
        sparse_dense_error < 1e-10,
        "max matrix-element difference < 1e-10",
        "Sparse expm_multiply versus the paper's dense scipy.linalg.expm path",
    )

    trace_error = float(abs(np.trace(sparse_rho) - 1.0))
    hermiticity_error = float(np.max(np.abs(sparse_rho - sparse_rho.conj().T)))
    minimum_eigenvalue = float(np.min(np.linalg.eigvalsh((sparse_rho + sparse_rho.conj().T) / 2)))
    checks["density_matrix_physicality"] = _check(
        {
            "trace_error": trace_error,
            "hermiticity_error": hermiticity_error,
            "minimum_eigenvalue": minimum_eigenvalue,
        },
        trace_error < 1e-10 and hermiticity_error < 1e-10 and minimum_eigenvalue > -1e-10,
        "trace/Hermiticity errors < 1e-10 and min eigenvalue > -1e-10",
        "Lindblad complete positivity and trace preservation",
    )

    clean_decay = PreparedTransport.from_seed(
        TransportModel(6, t_mean=0.0, delta_t=0.0), seed=0
    )
    times = np.linspace(0.0, 6.0, 61)
    dynamics = clean_decay.population_dynamics(ChannelRates(gamma_rec=1.0), times)
    normalized_dark = dynamics["dark"] / dynamics["dark"][0]
    analytic_dark = np.exp(-times)
    dark_error = float(np.max(np.abs(normalized_dark - analytic_dark)))
    checks["single_exponential_dark_decay"] = _check(
        dark_error,
        dark_error < 1e-10,
        "max |p_D/p_D(0)-exp(-t)| < 1e-10",
        "EQ005 in the ideal dark manifold",
    )

    ensemble = prepare_ensemble(TransportModel(6), range(15))
    rescue = ensemble_final_populations(
        ensemble, ChannelRates(gamma_rec=1.0), final_time=30.0
    )
    dephasing = ensemble_final_populations(
        ensemble, ChannelRates(gamma_deph=1.0), final_time=30.0
    )
    eta_rec = float(rescue["mean"]["sink"])
    eta_deph = float(dephasing["mean"]["sink"])
    checks["figure2_n6_endpoint"] = _check(
        {
            "generated_eta_rec": eta_rec,
            "generated_eta_deph": eta_deph,
            "paper_eta_rec": 0.999,
            "paper_eta_deph": 0.794,
        },
        abs(eta_rec - 0.999) < 0.01 and abs(eta_deph - 0.794) < 0.03,
        "rescue within 0.01 and dephasing within 0.03 of SM Table 2 at Delta=0",
        "Independent 15-realization cross-figure parameter check",
    )

    model_card = {
        "model": asdict(TransportModel(6)),
        "rates": asdict(ChannelRates(gamma_rec=1.0, gamma_deph=1.0)),
        "source_state": "|1><1|",
        "seeds": list(range(15)),
    }
    passed = all(item["passed"] for item in checks.values())
    return {
        "schema_version": 1,
        "check": "scientific_acceptance",
        "paper_id": "2608.05312",
        "status": "passed" if passed else "failed",
        "model_card": model_card,
        "checks": checks,
        "summary": {
            "passed": sum(item["passed"] for item in checks.values()),
            "total": len(checks),
        },
    }
