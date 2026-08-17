# Derivation Trace

## 1. Harper operator

For rational magnetic flux `alpha=p/q`, the printed difference equation is

`g[m+1] + g[m-1] + 2 cos(2 pi p m/q - nu) g[m] = epsilon g[m]`.

Imposing a total Bloch phase `theta` across the q-site magnetic cell turns it
into a q-by-q Hermitian matrix. The two bonds joining each pair are retained in
the q=2 case; for q=1 both hopping directions contribute to the diagonal. This
is `EQ001` and the sole microscopic numerical input.

## 2. Band edges without digitisation

Solving EQ001 for `g[m+1]` gives the transfer step

`A_m = [[epsilon - 2 cos(2 pi p m/q - nu), -1], [1, 0]]`.

One magnetic period is `Q=A_(q-1)...A_0`. The paper's Chambers reduction makes
the Bloch phases additive extrema of one degree-q trace polynomial. Therefore
the two opposite phase extrema produce 2q roots; after sorting, adjacent root
pairs are the q allowed bands. This matrix construction is checked independently
by substituting every test edge into the transfer product: `||Tr Q|-4|` is at
most `5.97e-12`.

## 3. Symmetries and bounds

Complex conjugation and index reflection give `sigma(alpha)=sigma(1-alpha)`.
The bipartite sign map gives energy inversion, and the two unit hoppings plus
the onsite cosine term give `|epsilon|<=4`. These identities are verified on
independent rational points rather than read from the plotted butterfly.

## 4. Skeleton and recursive cells

Fig. 2 uses all bands of the pure families `1/N` and `1-1/N` through `N=37`,
plus the central band for `N/(2N+1)` and `(N+1)/(2N+1)`. Its straight segments
connect computed band endpoints; no source coordinate is digitised.

For Fig. 3, the L2 cell is bounded by the leftmost bands at `alpha=1/5` and
`1/4`. Inverting the printed relation `alpha=1/(4+alpha')` gives
`alpha'=1/alpha-4` (orientation reversed). The interpolated cell boundaries are
affinely mapped to energies `[-4,4]`.

For Fig. 4, the C2 cell is bounded by the central bands at `alpha=2/5` and
`3/7`. The printed center-chain map gives
`alpha'=alpha/(1-2 alpha)-2`. The same affine energy normalization yields the
rectangularized subcell.

## 5. Field-smeared spectrum

Fig. 5 is the union of spectra within `delta-alpha=1/100`. A binary occupancy
raster is generated from independently computed band intervals, then dilated
only along the alpha direction by the printed window. The q cutoff and raster
size are declared convergence choices because the paper does not print them.

## 6. Wavefunction reordering

At each Fig. 6 rational flux, the largest periodic Harper eigenpair is computed.
If `p^{-1}` is the multiplicative inverse modulo q, the paper's traversal order
is `m_j = j p^{-1} mod q`. Inside the magnetic period `P=q/p`, this means
`x_j/P=j/q`. The exact sequence for the paper's worked `5/17` example is unit
tested, and each plotted amplitude vector is checked directly in EQ001.

All seven equation cards are machine-readable in `EQUATION_CARDS.json`; no
equation remains source-only or blocked.
