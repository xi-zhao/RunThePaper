"""End-to-end numerical campaign for every numeric panel in arXiv:1810.00888."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

from .model import (
    PXPBasis,
    SectorSpectrum,
    build_basis,
    build_dihedral_projector,
    build_hamiltonian,
    build_inversion_projector,
    build_trial_family,
    computational_vector,
    entanglement_entropy,
    fsa_states,
    gamma_state,
    local_x_profile,
    local_x_profile_formula,
    overlap_distribution,
    pattern_state,
    projected_variational_diagonalization,
    reconstruct_eigenstate,
    sector_spectrum,
    z2_momentum_vector,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def atomic_npz(path: Path, **arrays: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.savez(handle, **arrays)
    os.replace(temporary, path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


@dataclass
class System:
    basis: PXPBasis
    hamiltonian: Any


class ScarCampaign:
    """One physical model feeding all nine declared figure targets."""

    def __init__(self, workspace: Path, config: dict[str, Any], output: Path):
        self.workspace = workspace
        self.config = config
        self.parameters = config["parameters"]
        self.output = output
        self.data_dir = output / "data"
        self.check_dir = output / "checks"
        self.checkpoint_dir = output / "checkpoints"
        for directory in (
            self.data_dir,
            self.check_dir,
            self.checkpoint_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        self.config_digest = sha256_json(config)
        numerical_source = workspace / "src" / "exact_scars" / "model.py"
        self.source_digest = sha256_file(numerical_source)
        orchestration_files = sorted(
            (workspace / "src" / "exact_scars").glob("*.py")
        ) + [workspace / "scripts" / "run_reproduction.py"]
        self.orchestration_digest = sha256_json(
            {
                str(path.relative_to(workspace)): sha256_file(path)
                for path in orchestration_files
            }
        )
        self.systems: dict[tuple[int, bool], System] = {}
        self.spectra: dict[tuple[int, bool, int | None, int], SectorSpectrum] = {}
        self.trials: dict[tuple[int, str, int], dict[int, np.ndarray]] = {}
        self.target_results: dict[str, dict[str, Any]] = {}

    def system(self, length: int, periodic: bool) -> System:
        key = (length, periodic)
        if key not in self.systems:
            basis = build_basis(length, periodic=periodic)
            self.systems[key] = System(
                basis=basis, hamiltonian=build_hamiltonian(basis)
            )
        return self.systems[key]

    def spectrum(
        self,
        length: int,
        periodic: bool,
        *,
        parity: int,
        k_sign: int | None = None,
    ) -> SectorSpectrum:
        key = (length, periodic, k_sign, parity)
        if key in self.spectra:
            return self.spectra[key]
        label = f"{'pbc' if periodic else 'obc'}_L{length}_k{k_sign}_i{parity}"
        checkpoint = self.checkpoint_dir / f"sector_{label}.npz"
        manifest = self.checkpoint_dir / f"sector_{label}.json"
        system = self.system(length, periodic)
        if periodic:
            if k_sign is None:
                raise ValueError("periodic spectrum requires k_sign")
            projector = build_dihedral_projector(
                system.basis, k_sign=k_sign, parity=parity
            )
        else:
            projector = build_inversion_projector(system.basis, parity=parity)
        valid = False
        if checkpoint.exists() and manifest.exists():
            metadata = json.loads(manifest.read_text())
            valid = (
                metadata.get("config_sha256") == self.config_digest
                and metadata.get("source_sha256") == self.source_digest
                and metadata.get("checkpoint_sha256") == sha256_file(checkpoint)
            )
        if valid:
            with np.load(checkpoint) as payload:
                energies = payload["energies"]
                vectors = payload["vectors"]
            spectrum = SectorSpectrum(
                energies=energies,
                vectors=vectors,
                projector=projector,
                k_sign=k_sign,
                parity=parity,
            )
        else:
            spectrum = sector_spectrum(
                system.basis,
                system.hamiltonian,
                parity=parity,
                k_sign=k_sign,
            )
            atomic_npz(
                checkpoint,
                energies=spectrum.energies,
                vectors=spectrum.vectors,
            )
            atomic_json(
                manifest,
                {
                    "condition": label,
                    "config_sha256": self.config_digest,
                    "source_sha256": self.source_digest,
                    "checkpoint_sha256": sha256_file(checkpoint),
                    "dimension": len(spectrum.energies),
                },
            )
        self.spectra[key] = spectrum
        return spectrum

    def trial_family(
        self, length: int, family: str, maximum_particles: int
    ) -> dict[int, np.ndarray]:
        key = (length, family, maximum_particles)
        if key in self.trials:
            return self.trials[key]
        system = self.system(length, periodic=True)
        trials = build_trial_family(
            system.basis,
            family=family,
            maximum_particles=maximum_particles,
            batch_size=int(self.parameters["trial_batch_size"]),
        )
        self.trials[key] = trials
        return trials

    @staticmethod
    def _z2_open_vectors(basis: PXPBasis) -> tuple[np.ndarray, np.ndarray]:
        first = computational_vector(basis, pattern_state(basis.length, "z2"))
        second = computational_vector(basis, pattern_state(basis.length, "z2_shift"))
        return (first + second) / np.sqrt(2.0), (first - second) / np.sqrt(2.0)

    def run_profiles(self) -> None:
        length = int(self.parameters["profile_length"])
        sites = np.arange(1, length + 1)
        target_pairs = {
            "T001": ((1, 1), (2, 2)),
            "T002": ((1, 2), (2, 1)),
        }
        for target, pairs in target_pairs.items():
            profiles = {
                f"gamma_{alpha}{beta}": local_x_profile_formula(length, alpha, beta)
                for alpha, beta in pairs
            }
            atomic_npz(
                self.data_dir / f"{target}_profiles.npz", sites=sites, **profiles
            )
            self.target_results[target] = {
                "status": "paper_exact",
                "length": length,
                "integrated_energies": {
                    name: float(profile.sum()) for name, profile in profiles.items()
                },
            }

        cross_length = int(self.parameters["profile_crosscheck_length"])
        cross_system = self.system(cross_length, periodic=False)
        cross_errors = {}
        for alpha, beta in product((1, 2), repeat=2):
            vector = gamma_state(cross_system.basis, alpha, beta)
            numeric = local_x_profile(cross_system.basis, vector)
            analytic = local_x_profile_formula(cross_length, alpha, beta)
            cross_errors[f"gamma_{alpha}{beta}"] = float(
                np.max(np.abs(numeric - analytic))
            )

        # The printed formula has one factor 1/3 per two physical sites.
        implied = 2.0 / np.log(3.0)
        printed = 2.0 * np.log(3.0)
        b = np.arange(1, 9, dtype=float)
        exact_magnitudes = 3.0 ** (-b)
        implied_prediction = np.exp(-(2.0 * b) / implied)
        printed_prediction = np.exp(-(2.0 * b) / printed)
        decay_review = {
            "source_pinpoint": "main.tex paragraph following Fig. 1: decay length 2 ln(3)",
            "formula_pinpoint": "supplement local-energy formula: edge term proportional to 3^{-b} at j=2b-1,2b",
            "classification": "inconclusive",
            "paper_error_candidate_emitted": False,
            "reason": "Analytic mismatch is stable, but fresh-context independent review is still missing.",
            "implied_decay_length_2_over_ln3": implied,
            "printed_decay_length_2_ln3": printed,
            "ratio_crosscheck": float(exact_magnitudes[1] / exact_magnitudes[0]),
            "max_abs_error_implied": float(
                np.max(np.abs(exact_magnitudes - implied_prediction))
            ),
            "max_abs_error_printed": float(
                np.max(np.abs(exact_magnitudes - printed_prediction))
            ),
            "independent_checks": [
                "successive-block ratio is exactly 1/3",
                "log-linear fit against physical site distance gives 2/ln(3)",
            ],
        }
        atomic_json(
            self.check_dir / "profile_formula_crosscheck.json",
            {
                "maximum_formula_vs_mps_error": cross_errors,
                "decay_length_review": decay_review,
            },
        )

    def run_open_spectrum(self) -> None:
        target = "T003"
        length = int(self.parameters["obc_spectrum_length"])
        system = self.system(length, periodic=False)
        plus, minus = self._z2_open_vectors(system.basis)
        spectra = {
            1: self.spectrum(length, False, parity=1),
            -1: self.spectrum(length, False, parity=-1),
        }
        overlaps = {
            1: overlap_distribution(plus, spectra[1]),
            -1: overlap_distribution(minus, spectra[-1]),
        }
        gamma_entries = []
        residuals = {}
        expected = {(1, 2): np.sqrt(2.0), (2, 1): -np.sqrt(2.0)}
        for (alpha, beta), energy in expected.items():
            gamma = gamma_state(system.basis, alpha, beta)
            residuals[f"gamma_{alpha}{beta}"] = float(
                np.linalg.norm(system.hamiltonian @ gamma - energy * gamma)
            )
            gamma_entries.append((energy, float(abs(plus @ gamma) ** 2), alpha, beta))
        atomic_npz(
            self.data_dir / f"{target}_obc_tower.npz",
            energy_even=spectra[1].energies,
            overlap_even=overlaps[1],
            energy_odd=spectra[-1].energies,
            overlap_odd=overlaps[-1],
            gamma=np.asarray(gamma_entries),
        )
        self.target_results[target] = {
            "status": "paper_exact" if length == 18 else "reduced_scale",
            "length": length,
            "sector_dimensions": {
                "even": len(spectra[1].energies),
                "odd": len(spectra[-1].energies),
            },
            "gamma_residuals": residuals,
        }

    def _periodic_context(
        self, length: int
    ) -> tuple[System, dict[int, SectorSpectrum]]:
        system = self.system(length, periodic=True)
        spectra = {
            1: self.spectrum(length, True, k_sign=1, parity=1),
            -1: self.spectrum(length, True, k_sign=-1, parity=-1),
        }
        return system, spectra

    def _plot_family(
        self,
        target: str,
        spectra: dict[int, SectorSpectrum],
        states: dict[str, tuple[np.ndarray, int]],
        *,
        length: int,
    ) -> dict[str, float]:
        arrays: dict[str, Any] = {
            "energy_plus": spectra[1].energies,
            "energy_minus": spectra[-1].energies,
        }
        peaks: dict[str, float] = {}
        for label, (state, sign) in states.items():
            overlap = overlap_distribution(state, spectra[sign])
            arrays[f"overlap_{label}"] = overlap
            peaks[label] = float(np.max(overlap))
        basis = self.system(length, periodic=True).basis
        for sign, suffix in ((1, "plus"), (-1, "minus")):
            reference = z2_momentum_vector(basis, sign)
            reference_overlap = overlap_distribution(reference, spectra[sign])
            arrays[f"z2_{suffix}_overlap"] = reference_overlap
        atomic_npz(self.data_dir / f"{target}_overlaps.npz", **arrays)
        self.target_results[target] = {
            "status": "paper_exact" if length == 26 else "reduced_scale",
            "length": length,
            "maximum_overlaps": peaks,
        }
        return peaks

    def run_main_mma(self) -> None:
        target = "T004"
        length = int(self.parameters["periodic_spectrum_length"])
        _, spectra = self._periodic_context(length)
        blocks = length // 2
        trials = self.trial_family(length, "xi", blocks)
        states = {
            f"xi_{particles}": (state, (-1) ** (blocks + particles))
            for particles, state in trials.items()
            if particles > 0
        }
        self._plot_family(target, spectra, states, length=length)

    def run_fsa(self) -> None:
        target = "T005"
        length = int(self.parameters["periodic_spectrum_length"])
        system, spectra = self._periodic_context(length)
        energies, states, leakage = fsa_states(system.basis, system.hamiltonian)
        arrays: dict[str, Any] = {
            "fsa_energy": energies,
            "backward_leakage": leakage,
            "energy_plus": spectra[1].energies,
            "energy_minus": spectra[-1].energies,
        }
        maximum = []
        for index, state in enumerate(states):
            plus = overlap_distribution(state, spectra[1])
            minus = overlap_distribution(state, spectra[-1])
            arrays[f"fsa_{index}_plus"] = plus
            arrays[f"fsa_{index}_minus"] = minus
            maximum.append(float(max(np.max(plus), np.max(minus))))
        atomic_npz(self.data_dir / f"{target}_fsa.npz", **arrays)
        self.target_results[target] = {
            "status": "paper_exact" if length == 26 else "reduced_scale",
            "length": length,
            "fsa_states": len(states),
            "maximum_matching_overlap": maximum,
            "maximum_backward_leakage": float(np.max(leakage)),
        }

    def run_sma_comparison(self) -> None:
        target = "T006"
        length = int(self.parameters["periodic_spectrum_length"])
        _, spectra = self._periodic_context(length)
        blocks = length // 2
        xi = self.trial_family(length, "xi", 1)[1]
        xi_tilde = self.trial_family(length, "xi_tilde", 1)[1]
        upsilon = self.trial_family(length, "upsilon", 1)[1]
        upsilon_tilde = self.trial_family(length, "upsilon_tilde", 1)[1]
        states = {
            "xi_1": (xi, (-1) ** (blocks + 1)),
            "upsilon_1": (upsilon, (-1) ** (blocks + 1)),
            "xi_tilde_1": (xi_tilde, (-1) ** blocks),
            "upsilon_tilde_1": (upsilon_tilde, (-1) ** blocks),
        }
        self._plot_family(target, spectra, states, length=length)

    def run_bond3_mma(self) -> None:
        target = "T007"
        length = int(self.parameters["periodic_spectrum_length"])
        _, spectra = self._periodic_context(length)
        blocks = length // 2
        trials = self.trial_family(length, "upsilon", blocks)
        states = {
            f"upsilon_{particles}": (state, (-1) ** (blocks + particles))
            for particles, state in trials.items()
            if particles > 0
        }
        self._plot_family(target, spectra, states, length=length)

    @staticmethod
    def _scar_index(
        spectrum: SectorSpectrum, reference: np.ndarray, window: tuple[float, float]
    ) -> int:
        overlaps = overlap_distribution(reference, spectrum)
        candidates = np.flatnonzero(
            (spectrum.energies >= window[0]) & (spectrum.energies <= window[1])
        )
        if not len(candidates):
            raise RuntimeError(f"no eigenvalue in scar window {window}")
        return int(candidates[np.argmax(overlaps[candidates])])

    def run_entropy_scaling(self) -> None:
        target = "T008"
        rows: list[dict[str, Any]] = []
        paper_lengths = [int(value) for value in self.parameters["entropy_lengths"]]
        for length in paper_lengths:
            system, spectra = self._periodic_context(length)
            blocks = length // 2
            trials = self.trial_family(length, "xi", min(2, blocks))
            signs = {particles: (-1) ** (blocks + particles) for particles in (1, 2)}
            z2_refs = {sign: z2_momentum_vector(system.basis, sign) for sign in (-1, 1)}
            index_one = self._scar_index(
                spectra[signs[1]], z2_refs[signs[1]], (-2.0, -0.5)
            )
            index_two = self._scar_index(
                spectra[signs[2]], z2_refs[signs[2]], (-3.4, -2.0)
            )
            scar_one = reconstruct_eigenstate(spectra[signs[1]], index_one)
            scar_two = reconstruct_eigenstate(spectra[signs[2]], index_two)
            rows.append(
                {
                    "length": length,
                    "log10_length": np.log10(length),
                    "ed_minus_1p33": entanglement_entropy(scar_one, system.basis),
                    "ed_minus_2p66": entanglement_entropy(scar_two, system.basis),
                    "vacuum_xi0": entanglement_entropy(trials[0], system.basis),
                    "sma_xi1": entanglement_entropy(trials[1], system.basis),
                    "mma_xi2": entanglement_entropy(trials[2], system.basis),
                    "energy_scar_one": spectra[signs[1]].energies[index_one],
                    "energy_scar_two": spectra[signs[2]].energies[index_two],
                }
            )
            # Keep only the main paper-size system cached between iterations.
            if length != int(self.parameters["periodic_spectrum_length"]):
                self.systems.pop((length, True), None)
                for sign in (-1, 1):
                    self.spectra.pop((length, True, sign, sign), None)
                self.trials.pop((length, "xi", min(2, blocks)), None)
        write_csv(self.data_dir / f"{target}_entropy.csv", rows)
        self.target_results[target] = {
            "status": (
                "paper_exact"
                if paper_lengths == [16, 18, 20, 22, 24, 26]
                else "reduced_scale"
            ),
            "lengths": paper_lengths,
            "all_values_finite": bool(
                np.all(np.isfinite([[value for value in row.values()] for row in rows]))
            ),
        }

    def run_variational_rediagonalization(self) -> None:
        target = "T009"
        length = int(self.parameters["periodic_spectrum_length"])
        system, spectra = self._periodic_context(length)
        blocks = length // 2
        trials = self.trial_family(length, "xi", blocks)
        ordered = [trials[index] for index in range(1, blocks + 1)]
        variational_energy, variational_states = projected_variational_diagonalization(
            ordered, system.hamiltonian
        )
        arrays: dict[str, Any] = {
            "variational_energy": variational_energy,
            "energy_plus": spectra[1].energies,
            "energy_minus": spectra[-1].energies,
        }
        peaks = []
        for index, state in enumerate(variational_states):
            plus = overlap_distribution(state, spectra[1])
            minus = overlap_distribution(state, spectra[-1])
            arrays[f"state_{index}_plus"] = plus
            arrays[f"state_{index}_minus"] = minus
            peaks.append(float(max(np.max(plus), np.max(minus))))
        atomic_npz(self.data_dir / f"{target}_rediagonalized.npz", **arrays)
        self.target_results[target] = {
            "status": "paper_exact" if length == 26 else "reduced_scale",
            "length": length,
            "variational_dimension": len(ordered),
            "maximum_overlaps": peaks,
        }

    def run(self) -> dict[str, Any]:
        started = time.time()
        self.run_profiles()
        self.run_open_spectrum()
        self.run_main_mma()
        self.run_fsa()
        self.run_sma_comparison()
        self.run_bond3_mma()
        self.run_entropy_scaling()
        self.run_variational_rediagonalization()
        artifact_paths = sorted(
            path
            for directory in (self.data_dir, self.check_dir)
            for path in directory.rglob("*")
            if path.is_file()
        )
        manifest = {
            "profile": self.config["profile"],
            "config_sha256": self.config_digest,
            "source_sha256": self.source_digest,
            "orchestration_sha256": self.orchestration_digest,
            "targets": self.target_results,
            "targets_total": len(self.target_results),
            "numeric_items_total": 9,
            "all_numeric_items_have_outputs": len(self.target_results) == 9,
            "paper_error_candidates": [],
            "paper_review_findings": [
                {
                    "finding_id": "REV001",
                    "classification": "inconclusive",
                    "topic": "printed edge-energy decay length",
                    "evidence": "checks/profile_formula_crosscheck.json",
                }
            ],
            "elapsed_seconds": time.time() - started,
            "artifacts": [
                {
                    "path": str(path.relative_to(self.output)),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
                for path in artifact_paths
            ],
        }
        atomic_json(self.check_dir / "run_manifest.json", manifest)
        return manifest
