# Derivation trace

## 1. Spin chain to Majoranas

For

`a_(2l-1)=(prod_{m<l} sigma_m^x) sigma_l^z` and
`a_(2l)=(prod_{m<l} sigma_m^x) sigma_l^y`,

`sigma_l^x=i a_(2l-1) a_(2l)` and
`sigma_l^z sigma_(l+1)^z=i a_(2l) a_(2l+1)`.
Therefore Eq. (1) is `H=(i/4)a^T A a`, with alternating upper
off-diagonal entries `-2J(t), -2W, -2J(t), ...`. The `N-1` bond sum
is retained exactly: this is an open, not periodic, chain.

## 2. State evolution

The covariance `Gamma_mn=(i/2)<[a_m,a_n]>` obeys
`dot(Gamma)=A Gamma-Gamma A`. Its initial value is the Gaussian ground
state at `J=5W`, obtained from the spectral sign of `iA`. The ramp is
`J/W=5-t/tau_Q`, so the total physical duration is `5 tau_Q` and
`tau_0/tau_Q=hbar/(2W tau_Q)`.

## 3. Final observables

At `J=0`, every bulk canonical Majorana pair is a physical bond. Hence
`<K>=sum_l (1-Gamma_(2l,2l+1))/2`. The even-parity edge pair completes
the final fermion basis. Wick contractions give the first two moments
`A1=<M>` and `A2=<M^2>`, and the cited definitions give `F1` and `F2`.
The exact pure-Gaussian overlap with the even cat-state covariance is
computed as an additional falsification check; it is not substituted for
the paper's plotted bounds.

## 4. Static spectrum

Positive eigenvalues of `iA` are elementary excitation energies. Low
many-body gaps are sums of these energies. Even sums are accessible from
the even initial state; odd sums are parity-inaccessible. This gives the
complete scientific content of Fig. 2(a) without reading its plotted paths.

## 5. Independent cross-check

A periodic-chain momentum-mode solver independently evolves decoupled
two-level Bogoliubov modes. It is used only to check thermodynamic-limit
kink scaling and must never replace the open-chain primary output.
