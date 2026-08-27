"""Published waveform coefficients from Sun 2024 (DOI 10.1007/s11433-024-2478-8).

Every entry is transcribed verbatim from the main text / appendix and tagged with
its source location so the formula gate can trace it.  Numerical runners consume
these values directly; source figures and digitized curves are never inputs.

Units: coefficient lists feed ``waveforms.fourier_waveform`` (result in 2*pi*MHz).
Constant detunings are given directly in MHz (multiply by 2*pi at use site).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from waveforms import ConstantWaveform, FourierWaveform, TWO_PI, scaled


@dataclass(frozen=True)
class SinglePhotonProtocol:
    """A single-photon BAM/ORMD CZ protocol fully specified by the paper."""

    name: str
    source: str
    B_mhz: float                    # Rydberg blockade strength B / 2*pi  [MHz]
    delta_q_mhz: float              # Foerster energy penalty delta_q / 2*pi [MHz]
    omega1: object                  # buffer-atom Rabi waveform  (callable, rad/us)
    omega2: object                  # qubit-atom Rabi waveform   (callable, rad/us)
    delta1: object                  # buffer-atom detuning       (callable, rad/us)
    delta2: object                  # qubit-atom detuning        (callable, rad/us)
    notes: str = ""


# ---------------------------------------------------------------------------
# Figure 3 - single buffer atom, one-photon ground-Rydberg transition, B = 2*pi*50 MHz
# Main text page 4:
#   Fig. 3(a) hybrid modulation:
#     Omega_1 = 0.686 * Omega_2
#     Omega_2 : [112.83, -46.32, -11.51, 2.35, 0.193, -1.14]
#     Delta_1 : [40.14, 31.41, -6.14]      Delta_2 : [41.67, 32.23, -6.56]
#   Fig. 3(d) amplitude-only modulation (text labels it "Fig. 3(c)"):
#     Omega_1 : [124.49, -34.38, -28.36, 1.50, 10.93, -11.93]
#     Omega_2 : [153.58, -51.60, 2.09, -23.86, -33.57, 30.15]
#     Delta_1 = 2*pi*9.33 MHz (const)      Delta_2 = 2*pi*5.27 MHz (const)
# ---------------------------------------------------------------------------

_FIG3_OMEGA2_HYBRID = (112.83, -46.32, -11.51, 2.35, 0.193, -1.14)

FIG3_HYBRID = SinglePhotonProtocol(
    name="fig3_hybrid",
    source="Sun2024 main text p.4, Fig. 3(a-c)",
    B_mhz=50.0,
    delta_q_mhz=0.0,
    omega1=FourierWaveform(scaled(_FIG3_OMEGA2_HYBRID, 0.686)),
    omega2=FourierWaveform(_FIG3_OMEGA2_HYBRID),
    delta1=FourierWaveform((40.14, 31.41, -6.14)),
    delta2=FourierWaveform((41.67, 32.23, -6.56)),
    notes="Hybrid amplitude+frequency modulation, one-photon.",
)

FIG3_AMPLITUDE = SinglePhotonProtocol(
    name="fig3_amplitude",
    source="Sun2024 main text p.4, Fig. 3(d-f)",
    B_mhz=50.0,
    delta_q_mhz=0.0,
    omega1=FourierWaveform((124.49, -34.38, -28.36, 1.50, 10.93, -11.93)),
    omega2=FourierWaveform((153.58, -51.60, 2.09, -23.86, -33.57, 30.15)),
    delta1=ConstantWaveform(9.33),
    delta2=ConstantWaveform(5.27),
    notes="Amplitude-only modulation, constant detunings, one-photon.",
)

# ---------------------------------------------------------------------------
# Figure 5 - dual-pulse Doppler-insensitive single pulse, one-photon, B = 2*pi*50 MHz
# Main text page 6:
#   Omega_1 : [174.55, -33.89, -39.45, -18.46, -3.37, 7.20, -1.07, 1.76]
#   Omega_2 : [164.23, -57.66, 3.13, 6.80, -21.23, -11.14, -2.52, 0.50]
#   Delta_1 = 2*pi*3.768 MHz (const)   Delta_2 = 2*pi*3.093 MHz (const)
# ---------------------------------------------------------------------------

FIG5_SINGLE_PULSE = SinglePhotonProtocol(
    name="fig5_single_pulse",
    source="Sun2024 main text p.6, Fig. 5(a)",
    B_mhz=50.0,
    delta_q_mhz=0.0,
    omega1=FourierWaveform((174.55, -33.89, -39.45, -18.46, -3.37, 7.20, -1.07, 1.76)),
    omega2=FourierWaveform((164.23, -57.66, 3.13, 6.80, -21.23, -11.14, -2.52, 0.50)),
    delta1=ConstantWaveform(3.768),
    delta2=ConstantWaveform(3.093),
    notes="One pulse of the dual-pulse technique; zero-velocity CZ (Fig. 5b).",
)

# Appendix Fig. a6, p.12: B=2*pi*100 MHz, one-photon protocols.
_A6_OMEGA2_HYBRID = (111.45, -44.05, -11.36, 0.33, 1.33, -1.97)

A6_HYBRID = SinglePhotonProtocol(
    name="a6_hybrid",
    source="Sun2024 appendix p.12, Fig. a6(a-b)",
    B_mhz=100.0,
    delta_q_mhz=0.0,
    omega1=FourierWaveform(scaled(_A6_OMEGA2_HYBRID, 0.685)),
    omega2=FourierWaveform(_A6_OMEGA2_HYBRID),
    delta1=FourierWaveform((42.79, 33.82, -5.44)),
    delta2=FourierWaveform((42.79, 33.82, -5.44)),
    notes="Appendix B=100 MHz hybrid one-photon protocol.",
)

A6_AMPLITUDE = SinglePhotonProtocol(
    name="a6_amplitude",
    source="Sun2024 appendix p.12, Fig. a6(c-d)",
    B_mhz=100.0,
    delta_q_mhz=0.0,
    omega1=FourierWaveform((128.31, -35.90, -29.34, 1.79, 12.40, -13.11)),
    omega2=FourierWaveform((150.75, -50.32, 2.47, -24.40, -35.65, 32.53)),
    delta1=ConstantWaveform(9.24),
    delta2=ConstantWaveform(5.25),
    notes="Appendix B=100 MHz amplitude-only one-photon protocol.",
)

SINGLE_PHOTON_PROTOCOLS = {
    p.name: p
    for p in (
        FIG3_HYBRID,
        FIG3_AMPLITUDE,
        FIG5_SINGLE_PULSE,
        A6_HYBRID,
        A6_AMPLITUDE,
    )
}


# ---------------------------------------------------------------------------
# Two-photon ground-Rydberg protocols (appendix eqs. a5/a6).
# Main text page 5:  Delta_0 = 2*pi*5 GHz (one-photon detuning).
#   Fig. 4(a) hybrid modulation of Omega_p and delta:
#     Omega_1S = 2*pi*448.87 MHz, Omega_2S = 2*pi*343.82 MHz
#     Omega_1p : [3229.71, -1170.45, -239.25, -33.70, -43.47, -127.98]
#     Omega_2p : [2713.71, -909.89, -215.59, -106.97, -129.61, 5.20]
#     delta_1  : [-21.25, 6.44, -14.58]     delta_2 : [2.00, 6.04, -14.49]
#   Fig. 4(d) amplitude-only modulation of Omega_p:
#     Omega_1S = 2*pi*370.18 MHz, Omega_2S = 2*pi*321.13 MHz
#     Omega_1p : [3442.06, -1350.63, -150.75, -22.40, -81.41, -115.84]
#     Omega_2p : [3396.69, -885.46, -654.28, -205.05, 262.51, -216.07]
#     delta_1 = 2*pi*-4.03 MHz (const)      delta_2 = 2*pi*-2.00 MHz (const)
# Fig. 6 three-qubit Toffoli phase-gate part (main text page 6):
#     Omega_1S = 2*pi*472.49 MHz, Omega_2S = 2*pi*368.79 MHz
#     Omega_1p : [2828.10, -1469.66, -185.18, 285.37, 248.22, -292.80]
#     Omega_2p : [3683.49, -1374.63, -434.93, 69.95, -48.91, -53.22]
#     delta_1 = 2*pi*5.574 MHz (const)      delta_2 = 2*pi*-5.663 MHz (const)
# ---------------------------------------------------------------------------

DELTA0_MHZ = 5000.0  # one-photon detuning Delta_0 / 2*pi [MHz]


@dataclass(frozen=True)
class TwoPhotonProtocol:
    """A two-photon BAM CZ protocol (appendix eqs. a5/a6)."""

    name: str
    source: str
    B_mhz: float
    delta_q_mhz: float
    delta0_mhz: float
    omega1p: object     # buffer lower-leg Rabi (callable, rad/us)
    omega1s: float      # buffer upper-leg Rabi (constant, rad/us)
    omega2p: object     # qubit lower-leg Rabi (callable)
    omega2s: float      # qubit upper-leg Rabi (constant)
    delta1: object      # buffer two-photon detuning (callable)
    delta2: object      # qubit two-photon detuning (callable)
    notes: str = ""


FIG4_HYBRID = TwoPhotonProtocol(
    name="fig4_hybrid",
    source="Sun2024 main text p.5, Fig. 4(a-c)",
    B_mhz=50.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((3229.71, -1170.45, -239.25, -33.70, -43.47, -127.98)),
    omega1s=TWO_PI * 448.87,
    omega2p=FourierWaveform((2713.71, -909.89, -215.59, -106.97, -129.61, 5.20)),
    omega2s=TWO_PI * 343.82,
    delta1=FourierWaveform((-21.25, 6.44, -14.58)),
    delta2=FourierWaveform((2.00, 6.04, -14.49)),
    notes="Two-photon hybrid modulation of Omega_p and delta.",
)

FIG4_AMPLITUDE = TwoPhotonProtocol(
    name="fig4_amplitude",
    source="Sun2024 main text p.5, Fig. 4(d-f)",
    B_mhz=50.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((3442.06, -1350.63, -150.75, -22.40, -81.41, -115.84)),
    omega1s=TWO_PI * 370.18,
    omega2p=FourierWaveform((3396.69, -885.46, -654.28, -205.05, 262.51, -216.07)),
    omega2s=TWO_PI * 321.13,
    delta1=ConstantWaveform(-4.03),
    delta2=ConstantWaveform(-2.00),
    notes="Two-photon amplitude-only modulation of Omega_p.",
)

FIG6_TOFFOLI = TwoPhotonProtocol(
    name="fig6_toffoli",
    source="Sun2024 main text p.6-7, Fig. 6",
    B_mhz=50.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((2828.10, -1469.66, -185.18, 285.37, 248.22, -292.80)),
    omega1s=TWO_PI * 472.49,
    omega2p=FourierWaveform((3683.49, -1374.63, -434.93, 69.95, -48.91, -53.22)),
    omega2s=TWO_PI * 368.79,
    delta1=ConstantWaveform(5.574),
    delta2=ConstantWaveform(-5.663),
    notes="Phase-gate part of the three-qubit Toffoli/CCZ protocol.",
)

A7_HYBRID = TwoPhotonProtocol(
    name="a7_hybrid",
    source="Sun2024 appendix p.12, Fig. a7(a-b)",
    B_mhz=100.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((3234.43, -1086.98, -275.00, -93.96, -41.85, -119.42)),
    omega1s=TWO_PI * 442.41,
    omega2p=FourierWaveform((2850.37, -995.04, -196.13, -84.17, -28.95, -120.89)),
    omega2s=TWO_PI * 350.90,
    delta1=FourierWaveform((-21.68, 4.06, -19.20)),
    delta2=FourierWaveform((-3.57, 2.57, -18.87)),
    notes="Appendix B=100 MHz hybrid two-photon protocol.",
)

A7_AMPLITUDE = TwoPhotonProtocol(
    name="a7_amplitude",
    source="Sun2024 appendix p.12, Fig. a7(c-d)",
    B_mhz=100.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((3337.20, -767.85, -614.38, -41.25, -88.80, -156.33)),
    omega1s=TWO_PI * 381.88,
    omega2p=FourierWaveform((3624.89, -894.35, -690.53, -346.77, 247.19, -127.99)),
    omega2s=TWO_PI * 330.08,
    delta1=ConstantWaveform(-2.02),
    delta2=ConstantWaveform(-2.57),
    notes="Appendix B=100 MHz amplitude-only two-photon protocol.",
)

A8_HYBRID = TwoPhotonProtocol(
    name="a8_hybrid",
    source="Sun2024 appendix p.12, Fig. a8(a-b)",
    B_mhz=100.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((3244.11, -1061.56, -262.13, -112.21, 12.12, -198.28)),
    omega1s=TWO_PI * 440.79,
    omega2p=FourierWaveform((2825.37, -922.56, -302.26, -34.04, -65.55, -88.27)),
    omega2s=TWO_PI * 349.13,
    delta1=FourierWaveform((-36.85, 4.22, -25.95)),
    delta2=FourierWaveform((-11.85, 0.08, -17.50)),
    notes="Appendix hybrid protocol with residual end-qubit coupling B/64.",
)

A8_AMPLITUDE = TwoPhotonProtocol(
    name="a8_amplitude",
    source="Sun2024 appendix p.12, Fig. a8(c-d)",
    B_mhz=100.0, delta_q_mhz=0.0, delta0_mhz=DELTA0_MHZ,
    omega1p=FourierWaveform((3348.93, -726.20, -546.18, -159.50, -174.75, -67.84)),
    omega1s=TWO_PI * 382.25,
    omega2p=FourierWaveform((3671.33, -936.72, -622.74, -393.10, 216.80, -99.90)),
    omega2s=TWO_PI * 331.04,
    delta1=ConstantWaveform(-2.00),
    delta2=ConstantWaveform(-2.84),
    notes="Appendix amplitude-only protocol with residual end-qubit coupling B/64.",
)

TWO_PHOTON_PROTOCOLS = {
    p.name: p
    for p in (
        FIG4_HYBRID,
        FIG4_AMPLITUDE,
        FIG6_TOFFOLI,
        A7_HYBRID,
        A7_AMPLITUDE,
        A8_HYBRID,
        A8_AMPLITUDE,
    )
}
