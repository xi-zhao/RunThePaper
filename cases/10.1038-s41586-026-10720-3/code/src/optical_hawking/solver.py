"""GPU-first analytic-signal UPPE solver.

Two integrators share one nonlinear model:

* ``dopri5`` follows the paper's fixed-step Dormand-Prince method in the
  interaction picture and reuses its FSAL stage;
* ``ifrk4`` treats the stiff co-moving dispersion exactly and uses four
  nonlinear evaluations per step, making it the A100 speed path.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

import torch

from .analysis import spectral_power
from .model import PropagationConfig, PulseSpec, SimulationGrid
from .physical_dispersion import CleanRoomPCFDispersion


SCENARIO_NAMES = (
    "pump_probe_full",
    "pump_only_full",
    "pump_probe_without_conjugate_spm",
    "pump_only_without_conjugate_spm",
)


def build_counterfactual_batch(
    time_fs: torch.Tensor,
    pump: PulseSpec,
    probe: PulseSpec,
    complex_dtype: torch.dtype,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Build the four paper/counterfactual scenarios as one FFT batch."""

    pump_field = pump.field(time_fs, complex_dtype)
    probe_field = probe.field(time_fs, complex_dtype)
    initial_time = torch.stack(
        (
            pump_field + probe_field,
            pump_field,
            pump_field + probe_field,
            pump_field,
        )
    )
    # Columns are THG, SPM, and conjugated SPM.  Dividing the shared gamma by
    # three below makes the familiar 3|a|^2a term equal gamma_spm.
    term_weights = torch.tensor(
        ((1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 0.0), (1.0, 1.0, 0.0)),
        device=time_fs.device,
        dtype=time_fs.dtype,
    )
    return initial_time, term_weights


@dataclass
class PropagationResult:
    scenario_names: tuple[str, ...]
    omega_rad_fs: torch.Tensor
    initial_spectral_power: torch.Tensor
    final_spectral_power: torch.Tensor
    snapshots: dict[int, torch.Tensor]
    final_state_omega: torch.Tensor
    runtime_seconds: float
    steps: int
    rhs_evaluations: int
    maximum_embedded_relative_error: float | None
    device: str
    precision: str
    integrator: str


class AnalyticSignalUPPE:
    """Advance a batched positive-frequency analytic signal through the fibre."""

    def __init__(
        self,
        grid: SimulationGrid,
        config: PropagationConfig,
        dispersion: CleanRoomPCFDispersion | None = None,
        device: str | torch.device | None = None,
    ) -> None:
        config.validate()
        grid.validate()
        self.grid = grid
        self.config = config
        self.dispersion = dispersion or CleanRoomPCFDispersion()
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.time_fs, self.omega_rad_fs, self.positive_mask = grid.tensors(
            self.device, config.real_dtype
        )
        omega_prime = self.dispersion.omega_prime(self.omega_rad_fs)
        self.linear = (
            -1j * omega_prime / config.frame_velocity_mm_fs
        ).to(config.complex_dtype)
        pump_omega = torch.as_tensor(
            2.0 * torch.pi * 299.792458 / 800.0,
            device=self.device,
            dtype=config.real_dtype,
        )
        self.nonlinear_gamma = (
            (config.gamma_spm_w_inv_mm / 3.0)
            * torch.clamp_min(self.omega_rad_fs, 0.0)
            / pump_omega
        ).to(config.complex_dtype)
        half_phase = torch.exp(self.linear * (0.5 * config.step_mm))
        self.if_half_phase = half_phase
        self.if_full_phase = half_phase.square()
        self.if_inverse_half_phase = half_phase.conj()
        self.if_inverse_full_phase = self.if_full_phase.conj()
        # Dormand--Prince is applied to the interaction-picture state.  The
        # wide paper grid makes a direct explicit update of the linear
        # dispersion unnecessarily unstable; these phases integrate it
        # exactly at every Runge--Kutta stage.
        self.dopri_phases = tuple(
            torch.exp(self.linear * (stage * config.step_mm))
            for stage in (0.0, 1.0 / 5.0, 3.0 / 10.0, 4.0 / 5.0, 8.0 / 9.0, 1.0)
        )

    def project_positive(self, state_omega: torch.Tensor) -> torch.Tensor:
        return state_omega * self.positive_mask

    def nonlinear_rhs(
        self, state_omega: torch.Tensor, term_weights: torch.Tensor
    ) -> torch.Tensor:
        field = torch.fft.ifft(state_omega, dim=-1)
        intensity = field.abs().square()
        weights = term_weights.to(field.real.dtype)
        thg = field.pow(3) * weights[:, 0, None]
        spm = 3.0 * intensity * field * weights[:, 1, None]
        conjugated_spm = (
            3.0 * intensity * field.conj() * weights[:, 2, None]
        )
        nonlinear_omega = torch.fft.fft(thg + spm + conjugated_spm, dim=-1)
        return (
            1j
            * self.nonlinear_gamma
            * nonlinear_omega
            * self.positive_mask
        )

    def rhs(self, state_omega: torch.Tensor, term_weights: torch.Tensor) -> torch.Tensor:
        return self.linear * state_omega + self.nonlinear_rhs(state_omega, term_weights)

    def _ifrk4_step(
        self, state: torch.Tensor, term_weights: torch.Tensor
    ) -> torch.Tensor:
        h = self.config.step_mm
        k1 = self.nonlinear_rhs(state, term_weights)
        state_a = self.if_half_phase * (state + 0.5 * h * k1)
        k2 = self.if_inverse_half_phase * self.nonlinear_rhs(state_a, term_weights)
        state_b = self.if_half_phase * (state + 0.5 * h * k2)
        k3 = self.if_inverse_half_phase * self.nonlinear_rhs(state_b, term_weights)
        state_c = self.if_full_phase * (state + h * k3)
        k4 = self.if_inverse_full_phase * self.nonlinear_rhs(state_c, term_weights)
        interaction_state = state + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        return self.project_positive(self.if_full_phase * interaction_state)

    def _dopri5_step(
        self,
        state: torch.Tensor,
        term_weights: torch.Tensor,
        first_stage: torch.Tensor | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.config.step_mm
        _, p2, p3, p4, p5, p6 = self.dopri_phases

        def interaction_rhs(
            interaction_state: torch.Tensor, phase: torch.Tensor
        ) -> torch.Tensor:
            physical_state = phase * interaction_state
            return phase.conj() * self.nonlinear_rhs(physical_state, term_weights)

        k1 = (
            first_stage
            if first_stage is not None
            else self.nonlinear_rhs(state, term_weights)
        )
        k2 = interaction_rhs(state + h * (1.0 / 5.0) * k1, p2)
        k3 = interaction_rhs(
            state + h * (3.0 / 40.0 * k1 + 9.0 / 40.0 * k2), p3
        )
        k4 = interaction_rhs(
            state + h * (44.0 / 45.0 * k1 - 56.0 / 15.0 * k2 + 32.0 / 9.0 * k3),
            p4,
        )
        k5 = interaction_rhs(
            state
            + h
            * (
                19372.0 / 6561.0 * k1
                - 25360.0 / 2187.0 * k2
                + 64448.0 / 6561.0 * k3
                - 212.0 / 729.0 * k4
            ),
            p5,
        )
        k6 = interaction_rhs(
            state
            + h
            * (
                9017.0 / 3168.0 * k1
                - 355.0 / 33.0 * k2
                + 46732.0 / 5247.0 * k3
                + 49.0 / 176.0 * k4
                - 5103.0 / 18656.0 * k5
            ),
            p6,
        )
        fifth_order_interaction = self.project_positive(
            state
            + h
            * (
                35.0 / 384.0 * k1
                + 500.0 / 1113.0 * k3
                + 125.0 / 192.0 * k4
                - 2187.0 / 6784.0 * k5
                + 11.0 / 84.0 * k6
            )
        )
        fifth_order = self.project_positive(p6 * fifth_order_interaction)
        k7_interaction = p6.conj() * self.nonlinear_rhs(fifth_order, term_weights)
        fourth_order_interaction = self.project_positive(
            state
            + h
            * (
                5179.0 / 57600.0 * k1
                + 7571.0 / 16695.0 * k3
                + 393.0 / 640.0 * k4
                - 92097.0 / 339200.0 * k5
                + 187.0 / 2100.0 * k6
                + 1.0 / 40.0 * k7_interaction
            )
        )
        # Transform the FSAL derivative into the next step's local interaction
        # picture.  The phase cancels analytically, leaving N(y_{n+1}).
        next_first_stage = p6 * k7_interaction
        embedded_error = p6 * (fifth_order_interaction - fourth_order_interaction)
        return fifth_order, next_first_stage, embedded_error

    def propagate(
        self,
        initial_time: torch.Tensor,
        term_weights: torch.Tensor,
        scenario_names: tuple[str, ...] = SCENARIO_NAMES,
    ) -> PropagationResult:
        if initial_time.ndim != 2:
            raise ValueError("initial_time must have shape [scenario, time]")
        if initial_time.shape[0] != term_weights.shape[0]:
            raise ValueError("scenario and term-weight batch sizes differ")
        state = self.project_positive(torch.fft.fft(initial_time, dim=-1))
        initial_power = spectral_power(state).detach().cpu()
        snapshot_count = max(0, self.config.record_snapshots)
        snapshot_steps = {
            round(index * self.config.steps / snapshot_count)
            for index in range(1, snapshot_count + 1)
        } if snapshot_count else set()
        snapshots: dict[int, torch.Tensor] = {}
        maximum_error_tensor = (
            torch.zeros((), device=self.device, dtype=self.config.real_dtype)
            if self.config.integrator == "dopri5"
            else None
        )
        first_stage: torch.Tensor | None = None

        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        started = time.perf_counter()

        if self.config.integrator == "ifrk4":
            step_function: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] = self._ifrk4_step
            if self.config.compile_step:
                step_function = torch.compile(step_function, mode="reduce-overhead")
            for step in range(1, self.config.steps + 1):
                state = step_function(state, term_weights)
                if step in snapshot_steps:
                    snapshots[step] = spectral_power(state).detach().cpu()
            rhs_evaluations = 4 * self.config.steps
        else:
            for step in range(1, self.config.steps + 1):
                state, first_stage, embedded_error = self._dopri5_step(
                    state, term_weights, first_stage
                )
                scale = torch.clamp_min(state.abs().amax(), 1.0e-30)
                relative_error = embedded_error.abs().amax() / scale
                maximum_error_tensor = torch.maximum(
                    maximum_error_tensor, relative_error
                )
                if step in snapshot_steps:
                    snapshots[step] = spectral_power(state).detach().cpu()
            rhs_evaluations = 1 + 6 * self.config.steps

        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        runtime = time.perf_counter() - started
        maximum_error = (
            float(maximum_error_tensor.detach().cpu())
            if maximum_error_tensor is not None
            else None
        )
        return PropagationResult(
            scenario_names=scenario_names,
            omega_rad_fs=self.omega_rad_fs.detach().cpu(),
            initial_spectral_power=initial_power,
            final_spectral_power=spectral_power(state).detach().cpu(),
            snapshots=snapshots,
            final_state_omega=state.detach().cpu(),
            runtime_seconds=runtime,
            steps=self.config.steps,
            rhs_evaluations=rhs_evaluations,
            maximum_embedded_relative_error=maximum_error,
            device=str(self.device),
            precision=self.config.precision,
            integrator=self.config.integrator,
        )
