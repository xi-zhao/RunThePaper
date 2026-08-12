# Numerical Methods

## Independent validation lane

- model: four-site periodic spinful extended Hubbard model;
- sectors: N=4 and N plus or minus 1;
- solver: dense Hermitian exact diagonalization;
- grid: 801 points from -12 to 12 eV;
- broadening: 0.08 eV;
- outputs: Lehmann Green function, self-energy, full/local DOS, bath strengths,
  and shell-resolved correction;
- isolation: raw/reference directories, network, and subprocesses blocked.

## Paper-scale lane

- independent periodic PySCF KRKS/KRHF entrypoint;
- paper-named bases, pseudopotentials, k meshes, and embedding sizes;
- independently reconstructed standard crystal structures;
- 16 material/reference/embedding-size work units;
- 16-way deterministic sharding;
- atomic stage markers bound to config, implementation, and result hashes;
- explicit mean-field, localization, bath, projection, correlated-solver,
  assembly, GW replacement, and observable stages.

The production periodic GW and approximately 200-orbital real-axis EOM-CCSD
Green-function solve has not run. The runner stops rather than substituting a
toy self-energy.
