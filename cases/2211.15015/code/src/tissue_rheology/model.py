"""Independent implementation of the active sheared vertex model."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .geometry import (
    PolygonObservables,
    edge_length,
    polygon_observables,
    remap_tilt,
    unwrap_cycle,
    wrap_fractional,
)
from .topology import (
    build_hexagonal_tiling,
    edge_map,
    perform_short_edge_t1s,
    validate_topology,
    vertex_cells,
)

FloatArray = NDArray[np.float64]


@dataclass
class StepResult:
    energy: float
    shear_stress: float
    raw_shear_stress: float
    t1_events: int
    unresolved_short_edges: int


class VertexTissue:
    """A periodic trivalent polygonal tissue with mutable T1 topology."""

    def __init__(
        self,
        *,
        lattice: FloatArray,
        fractional: FloatArray,
        cells: list[list[int]],
        target_area: FloatArray,
        target_perimeter: FloatArray,
        theta: FloatArray,
        rng: np.random.Generator,
        kappa_area: float = 0.5,
        kappa_perimeter: float = 1.0,
        zeta: float = 1.0,
        rotational_diffusion: float = 0.5,
        t1_threshold: float = 0.07,
        t1_reset_factor: float = 1.5,
        time: float = 0.0,
        strain: float = 0.0,
        t1_count: int = 0,
    ) -> None:
        self.lattice = np.asarray(lattice, dtype=np.float64)
        self.fractional = wrap_fractional(fractional)
        self.cells = [[int(vertex) for vertex in cycle] for cycle in cells]
        self.target_area = np.asarray(target_area, dtype=np.float64)
        self.target_perimeter = np.asarray(target_perimeter, dtype=np.float64)
        self.theta = np.asarray(theta, dtype=np.float64)
        self.rng = rng
        self.kappa_area = float(kappa_area)
        self.kappa_perimeter = float(kappa_perimeter)
        self.zeta = float(zeta)
        self.rotational_diffusion = float(rotational_diffusion)
        self.t1_threshold = float(t1_threshold)
        self.t1_reset_factor = float(t1_reset_factor)
        self.time = float(time)
        self.strain = float(strain)
        self.t1_count = int(t1_count)
        self._validate_state()

    @classmethod
    def initialize(
        cls,
        *,
        nx: int,
        ny: int,
        p0: float,
        seed: int,
        kappa_area: float = 0.5,
        kappa_perimeter: float = 1.0,
        zeta: float = 1.0,
        rotational_diffusion: float = 0.5,
        t1_threshold: float = 0.07,
        t1_reset_factor: float = 1.5,
        bidispersity: float = 1.4,
    ) -> "VertexTissue":
        lattice, fractional, cells = build_hexagonal_tiling(nx, ny)
        cell_count = len(cells)
        if cell_count % 2:
            raise ValueError("the 1:1 bidisperse packing requires an even cell count")
        if p0 <= 0.0 or bidispersity <= 0.0:
            raise ValueError("p0 and bidispersity must be positive")
        total_area = float(np.linalg.det(lattice))
        small_area = 2.0 * total_area / (cell_count * (1.0 + bidispersity**2))
        target_area = np.full(cell_count, small_area, dtype=np.float64)
        rng = np.random.default_rng(seed)
        large = rng.choice(cell_count, size=cell_count // 2, replace=False)
        target_area[large] *= bidispersity**2
        target_perimeter = p0 * np.sqrt(target_area)
        theta = rng.uniform(0.0, 2.0 * np.pi, size=cell_count)
        return cls(
            lattice=lattice,
            fractional=fractional,
            cells=cells,
            target_area=target_area,
            target_perimeter=target_perimeter,
            theta=theta,
            rng=rng,
            kappa_area=kappa_area,
            kappa_perimeter=kappa_perimeter,
            zeta=zeta,
            rotational_diffusion=rotational_diffusion,
            t1_threshold=t1_threshold,
            t1_reset_factor=t1_reset_factor,
        )

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    @property
    def vertex_count(self) -> int:
        return len(self.fractional)

    def _validate_state(self) -> None:
        if self.lattice.shape != (2, 2) or np.linalg.det(self.lattice) <= 0.0:
            raise ValueError("lattice must be a positive-orientation 2x2 matrix")
        if self.fractional.shape != (self.vertex_count, 2):
            raise ValueError("fractional coordinates must have shape (V,2)")
        if len(self.target_area) != self.cell_count:
            raise ValueError("one target area is required per cell")
        if len(self.target_perimeter) != self.cell_count:
            raise ValueError("one target perimeter is required per cell")
        if len(self.theta) != self.cell_count:
            raise ValueError("one polarization angle is required per cell")
        if np.any(self.target_area <= 0.0) or np.any(self.target_perimeter <= 0.0):
            raise ValueError("target geometry must be positive")
        if self.kappa_area <= 0.0 or self.kappa_perimeter <= 0.0 or self.zeta <= 0.0:
            raise ValueError("elastic moduli and drag must be positive")
        validate_topology(self.cells, self.vertex_count)
        self.cell_observables()

    def copy(self) -> "VertexTissue":
        generator = np.random.default_rng()
        generator.bit_generator.state = json.loads(
            json.dumps(self.rng.bit_generator.state)
        )
        return VertexTissue(
            lattice=self.lattice.copy(),
            fractional=self.fractional.copy(),
            cells=[cycle.copy() for cycle in self.cells],
            target_area=self.target_area.copy(),
            target_perimeter=self.target_perimeter.copy(),
            theta=self.theta.copy(),
            rng=generator,
            kappa_area=self.kappa_area,
            kappa_perimeter=self.kappa_perimeter,
            zeta=self.zeta,
            rotational_diffusion=self.rotational_diffusion,
            t1_threshold=self.t1_threshold,
            t1_reset_factor=self.t1_reset_factor,
            time=self.time,
            strain=self.strain,
            t1_count=self.t1_count,
        )

    def cell_observables(self) -> list[PolygonObservables]:
        return [
            polygon_observables(unwrap_cycle(self.fractional, cycle, self.lattice))
            for cycle in self.cells
        ]

    def elastic_energy(self) -> float:
        observables = self.cell_observables()
        area = np.array([item.area for item in observables])
        perimeter = np.array([item.perimeter for item in observables])
        return float(
            0.5 * self.kappa_area * np.sum((area - self.target_area) ** 2)
            + 0.5
            * self.kappa_perimeter
            * np.sum((perimeter - self.target_perimeter) ** 2)
        )

    def elastic_forces(
        self,
    ) -> tuple[FloatArray, list[FloatArray], list[PolygonObservables]]:
        total = np.zeros_like(self.fractional)
        cell_forces: list[FloatArray] = []
        observables = self.cell_observables()
        for cell_index, (cycle, item) in enumerate(
            zip(self.cells, observables, strict=True)
        ):
            contribution = -self.kappa_area * (item.area - self.target_area[cell_index])
            contribution = contribution * item.grad_area
            contribution -= (
                self.kappa_perimeter
                * (item.perimeter - self.target_perimeter[cell_index])
                * item.grad_perimeter
            )
            cell_forces.append(contribution)
            for local_index, vertex in enumerate(cycle):
                total[vertex] += contribution[local_index]
        return total, cell_forces, observables

    def active_forces(self, activity: float) -> FloatArray:
        if activity == 0.0:
            return np.zeros_like(self.fractional)
        incidence = vertex_cells(self.cells, self.vertex_count)
        output = np.zeros_like(self.fractional)
        for vertex, owners in enumerate(incidence):
            if len(owners) != 3:
                raise ValueError("active weighting requires a trivalent vertex")
            neighbors: set[int] = set()
            local_lengths: dict[int, float] = {}
            for cell in owners:
                cycle = self.cells[cell]
                index = cycle.index(vertex)
                previous = cycle[index - 1]
                following = cycle[(index + 1) % len(cycle)]
                neighbors.update((previous, following))
                local_lengths[cell] = edge_length(
                    self.fractional, vertex, previous, self.lattice
                ) + edge_length(self.fractional, vertex, following, self.lattice)
            if len(neighbors) != 3:
                raise ValueError(
                    "trivalent vertex must have three distinct incident edges"
                )
            total_incident_length = sum(
                edge_length(self.fractional, vertex, neighbor, self.lattice)
                for neighbor in neighbors
            )
            if total_incident_length <= 0.0:
                raise ValueError("incident edge length must be positive")
            for cell in owners:
                weight = local_lengths[cell] / (12.0 * total_incident_length)
                direction = np.array(
                    [np.cos(self.theta[cell]), np.sin(self.theta[cell])],
                    dtype=np.float64,
                )
                output[vertex] += activity * weight * direction
        return output

    def cell_stress_tensors(
        self,
    ) -> tuple[FloatArray, list[FloatArray], list[PolygonObservables]]:
        _, cell_forces, observables = self.elastic_forces()
        tensors = np.empty((self.cell_count, 2, 2), dtype=np.float64)
        for cell, (forces, item) in enumerate(
            zip(cell_forces, observables, strict=True)
        ):
            relative = item.vertices - item.centroid
            tensors[cell] = np.einsum("ia,ib->ab", forces, relative) / item.area
        return tensors, cell_forces, observables

    def raw_shear_stress(self) -> float:
        tensors, _, _ = self.cell_stress_tensors()
        return float(np.mean(tensors[:, 0, 1]))

    def shear_stress(self) -> float:
        """Return positive resistance for positive imposed shear.

        Equation (6) fixes the signed raw virial. The paper plots the positive
        resistance magnitude, so the observable stores its absolute value while
        retaining the signed value in every sampled step.
        """

        return float(abs(self.raw_shear_stress()))

    def tension_network(self) -> list[dict[str, float | int]]:
        observables = self.cell_observables()
        output: list[dict[str, float | int]] = []
        for key, records in edge_map(self.cells).items():
            first_cell = records[0].cell
            second_cell = records[1].cell
            tension = self.kappa_perimeter * (
                observables[first_cell].perimeter
                - self.target_perimeter[first_cell]
                + observables[second_cell].perimeter
                - self.target_perimeter[second_cell]
            )
            displacement = self._edge_displacement(key[0], key[1])
            output.append(
                {
                    "first": key[0],
                    "second": key[1],
                    "length": float(np.linalg.norm(displacement)),
                    "tension": float(max(tension, 0.0)),
                }
            )
        return output

    def _edge_displacement(self, first: int, second: int) -> FloatArray:
        from .geometry import edge_displacement

        return edge_displacement(self.fractional, first, second, self.lattice)

    def unresolved_short_edge_count(self) -> int:
        return sum(
            edge_length(self.fractional, key[0], key[1], self.lattice)
            < self.t1_threshold
            for key in edge_map(self.cells)
        )

    def step(
        self,
        *,
        activity: float,
        shear_rate: float,
        dt: float,
        enable_t1: bool = True,
        max_t1_events: int = 16,
        max_nonaffine_displacement: float | None = None,
    ) -> StepResult:
        if dt <= 0.0 or shear_rate < 0.0 or activity < 0.0:
            raise ValueError("dt must be positive and activity/shear rate nonnegative")
        elastic, _, _ = self.elastic_forces()
        nonaffine_velocity = (elastic + self.active_forces(activity)) / self.zeta
        displacement = dt * nonaffine_velocity
        if max_nonaffine_displacement is not None:
            norms = np.linalg.norm(displacement, axis=1)
            scale = np.minimum(
                1.0, max_nonaffine_displacement / np.maximum(norms, 1e-30)
            )
            displacement *= scale[:, None]
        inverse = np.linalg.inv(self.lattice)
        self.fractional += (inverse @ displacement.T).T
        self.fractional = wrap_fractional(self.fractional)

        self.theta += np.sqrt(2.0 * self.rotational_diffusion * dt) * self.rng.normal(
            size=self.cell_count
        )
        self.theta = np.mod(self.theta, 2.0 * np.pi)

        self.lattice[0, 1] += shear_rate * self.lattice[1, 1] * dt
        self.fractional, self.lattice, _ = remap_tilt(self.fractional, self.lattice)

        events: list[dict[str, int]] = []
        if enable_t1:
            self.cells, self.fractional, events = perform_short_edge_t1s(
                self.cells,
                self.fractional,
                self.lattice,
                self.t1_threshold,
                self.t1_reset_factor,
                max_t1_events,
            )
            self.t1_count += len(events)

        self.time += dt
        self.strain += shear_rate * dt
        if not np.all(np.isfinite(self.fractional)):
            raise FloatingPointError("nonfinite vertex coordinate")
        energy = self.elastic_energy()
        raw_stress = self.raw_shear_stress()
        return StepResult(
            energy=energy,
            shear_stress=float(abs(raw_stress)),
            raw_shear_stress=raw_stress,
            t1_events=len(events),
            unresolved_short_edges=self.unresolved_short_edge_count(),
        )

    def run(
        self,
        *,
        steps: int,
        activity: float,
        shear_rate: float,
        dt: float,
        sample_every: int,
        enable_t1: bool = True,
        max_nonaffine_displacement: float | None = None,
        checkpoint_every: int | None = None,
        checkpoint_path: Path | None = None,
        checkpoint_binding: dict[str, str] | None = None,
        starting_step: int = 0,
    ) -> dict[str, FloatArray]:
        if steps < 0 or sample_every <= 0:
            raise ValueError("steps must be nonnegative and sample_every positive")
        times: list[float] = []
        strains: list[float] = []
        stresses: list[float] = []
        energies: list[float] = []
        t1_counts: list[float] = []
        unresolved: list[float] = []
        for local_step in range(steps):
            result = self.step(
                activity=activity,
                shear_rate=shear_rate,
                dt=dt,
                enable_t1=enable_t1,
                max_nonaffine_displacement=max_nonaffine_displacement,
            )
            absolute_step = starting_step + local_step + 1
            if absolute_step % sample_every == 0 or local_step == steps - 1:
                times.append(self.time)
                strains.append(self.strain)
                stresses.append(result.shear_stress)
                energies.append(result.energy)
                t1_counts.append(float(self.t1_count))
                unresolved.append(float(result.unresolved_short_edges))
            if (
                checkpoint_every
                and checkpoint_path is not None
                and absolute_step % checkpoint_every == 0
            ):
                self.save_checkpoint(
                    checkpoint_path,
                    binding=checkpoint_binding or {},
                    completed_steps=absolute_step,
                )
        return {
            "time": np.asarray(times, dtype=np.float64),
            "strain": np.asarray(strains, dtype=np.float64),
            "stress": np.asarray(stresses, dtype=np.float64),
            "energy": np.asarray(energies, dtype=np.float64),
            "t1_count": np.asarray(t1_counts, dtype=np.float64),
            "unresolved_short_edges": np.asarray(unresolved, dtype=np.float64),
        }

    def state_digest(self) -> str:
        digest = hashlib.sha256()
        for array in (
            self.lattice,
            self.fractional,
            self.target_area,
            self.target_perimeter,
            self.theta,
        ):
            digest.update(np.asarray(array).tobytes(order="C"))
        digest.update(json.dumps(self.cells, separators=(",", ":")).encode("utf-8"))
        digest.update(
            json.dumps(
                {
                    "time": self.time,
                    "strain": self.strain,
                    "t1_count": self.t1_count,
                    "rng": self.rng.bit_generator.state,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return digest.hexdigest()

    def _flatten_cells(self) -> tuple[NDArray[np.int64], NDArray[np.int64]]:
        offsets = np.zeros(self.cell_count + 1, dtype=np.int64)
        for index, cycle in enumerate(self.cells):
            offsets[index + 1] = offsets[index] + len(cycle)
        flat = np.asarray(
            [vertex for cycle in self.cells for vertex in cycle], dtype=np.int64
        )
        return flat, offsets

    def save_checkpoint(
        self,
        path: Path,
        *,
        binding: dict[str, str],
        completed_steps: int,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        flat, offsets = self._flatten_cells()
        metadata = {
            "binding": binding,
            "completed_steps": int(completed_steps),
            "time": self.time,
            "strain": self.strain,
            "t1_count": self.t1_count,
            "kappa_area": self.kappa_area,
            "kappa_perimeter": self.kappa_perimeter,
            "zeta": self.zeta,
            "rotational_diffusion": self.rotational_diffusion,
            "t1_threshold": self.t1_threshold,
            "t1_reset_factor": self.t1_reset_factor,
            "rng_state": self.rng.bit_generator.state,
            "state_sha256": self.state_digest(),
        }
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        with temporary.open("wb") as handle:
            np.savez_compressed(
                handle,
                lattice=self.lattice,
                fractional=self.fractional,
                target_area=self.target_area,
                target_perimeter=self.target_perimeter,
                theta=self.theta,
                cell_flat=flat,
                cell_offsets=offsets,
                metadata_json=np.asarray(json.dumps(metadata, sort_keys=True)),
            )
        os.replace(temporary, path)

    @classmethod
    def load_checkpoint(
        cls,
        path: Path,
        *,
        expected_binding: dict[str, str] | None = None,
    ) -> tuple["VertexTissue", int, dict[str, Any]]:
        with np.load(path, allow_pickle=False) as payload:
            metadata = json.loads(str(payload["metadata_json"]))
            if (
                expected_binding is not None
                and metadata.get("binding") != expected_binding
            ):
                raise ValueError(
                    "checkpoint binding does not match config/implementation hashes"
                )
            flat = payload["cell_flat"].astype(np.int64)
            offsets = payload["cell_offsets"].astype(np.int64)
            cells = [
                flat[offsets[index] : offsets[index + 1]].astype(int).tolist()
                for index in range(len(offsets) - 1)
            ]
            generator = np.random.default_rng()
            generator.bit_generator.state = metadata["rng_state"]
            model = cls(
                lattice=payload["lattice"],
                fractional=payload["fractional"],
                cells=cells,
                target_area=payload["target_area"],
                target_perimeter=payload["target_perimeter"],
                theta=payload["theta"],
                rng=generator,
                kappa_area=metadata["kappa_area"],
                kappa_perimeter=metadata["kappa_perimeter"],
                zeta=metadata["zeta"],
                rotational_diffusion=metadata["rotational_diffusion"],
                t1_threshold=metadata["t1_threshold"],
                t1_reset_factor=metadata["t1_reset_factor"],
                time=metadata["time"],
                strain=metadata["strain"],
                t1_count=metadata["t1_count"],
            )
        if model.state_digest() != metadata["state_sha256"]:
            raise ValueError("checkpoint state hash mismatch")
        return model, int(metadata["completed_steps"]), metadata
