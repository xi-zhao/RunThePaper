# Formula Verification

All nine formula cards are open for numerics. Each card has a source trace, a derivation or numeric check, and a code pointer.

| Formula | Role | Gate | Check |
| --- | --- | --- | --- |
| EQ001--EQ003 | squeezed state and overlap | open | closed form vs 120-term sum: `8.77e-13` error |
| EQ004 | real kernel | open | symmetric, unit diagonal, minimum Gram eigenvalue `0.8572` |
| EQ005 | SVC | open | named datasets pass test-accuracy floor; capacity rises with `c` |
| EQ006 | perceptron | open | finite Fock training reaches accuracy 1 |
| EQ007--EQ008 | gate circuit and measurement | open | 4 blocks/32 parameters; loss ratio `0.0114` |
| EQ009 | corrected finite-set separability condition | open | Fock/analytic Gram error `9.77e-12`; 64/64 labels; two exact counterexamples |

Machine-readable outputs: `EQUATION_CARDS.json`, `outputs/checks/formula_verification.json`, and `outputs/checks/scientific_formula_checks.json`.
