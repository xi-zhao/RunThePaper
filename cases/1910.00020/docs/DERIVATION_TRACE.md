# Derivation Trace

| Formula | Source | Independent reasoning | Code | Gate |
| --- | --- | --- | --- | --- |
| EQ001 `S_Q` | main text order-parameter equation | coherent information reduces to trajectory-averaged reference entropy | `StabilizerState.entropy`, `_one_reference_survival` | verified |
| EQ002 stabilizer entropy | stabilizer method + binary derivation | restricted-generator rank counts crossing constraints | `gf2_rank`, `entropy` | verified |
| EQ003 finite-size scaling | equation after Fig. 1 | rescale independently generated curves | `_run_transition` | verified |
| EQ004 `Delta S_Q(x,t)` | Fig. 2/S1 captions | compare entropy immediately before/after each measurement | `_decoding_heatmap` | verified |
| EQ005 surface power law | Fig. 3(a) text | fit largest reduced size below `p_c` | `_run_surface_order` | verified, finite-size drift |
| EQ006 mutual-information scaling | equation before Fig. 3 discussion | compute three stabilizer entropies per trajectory | `_two_reference_curve` | verified |
| EQ007 purification power law | Supplement Eq. S1 | fit early-time log slope before finite-size turnover | `_run_supp_purification` | verified, reduced scale |
| EQ008 incomplete-record entropy | Fig. 2(b) retained-record protocol + mixed-stabilizer derivation | physically apply all measurements; dephase only unknown outcomes; use stabilizer-subgroup nullity | `MixedStabilizerState`, `_cutoff_curve` | verified |

The full derivation and the resolved T003 method-equivalence defect are in `DERIVATION.md`.
