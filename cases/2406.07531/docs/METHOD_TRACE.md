# Method Trace

| ID | Paper method | Independent implementation | Current state |
| --- | --- | --- | --- |
| NUM001 | B_DM, B_GF, B_NO interacting bath | baths.py | exact small-system tests passed |
| NUM002 | projected Hamiltonian and real-axis correlated Green function | embedding.py, ed.py, pyscf_backend.py | exact small-system path passed; production EOM-CCSD deferred |
| NUM003 | democratic assembly and GW replacement | embedding.py | algebra tests passed; material campaign deferred |
| NUM004 | Dyson spectra and observables | spectra.py | exact small-system tests passed; material campaign deferred |

The paper-scale runner validates 16 work units spanning every paper target and
records resource, checkpoint, hash, and fail-closed contracts.
