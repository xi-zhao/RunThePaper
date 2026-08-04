# Derivation

## One main hypothesis

The primary hypothesis is that the frozen PPB geometry comes from a
factor-of-two transcription error in the strong-disorder numerator.

## Frozen `N=3` numerator

Write `w_j=Delta_j-i/2`, `z_j=1/w_j`, and
`P=w_1 w_2 w_3`. Elementary expansion gives

$$
P=s_3-\frac{i}{2}s_2-\frac14s_1+\frac{i}{8},
$$

$$
\sum_{j<k}w_jw_k=s_2-is_1-\frac34,
\qquad \sum_jw_j=s_1-\frac{3i}{2}.
$$

Substitution into
`P F_frozen = P + (i/2) sum_{j<k} w_jw_k - (1/2) sum_j w_j`
leaves `s_3-s_1/4+i/2`. Since `P` never vanishes for finite real detunings,
`F_frozen` never vanishes.

## Source repair and global minimizer

Replacing `i/2` by the source coefficient `i` yields the two real equations

$$
s_2=-\frac14,\qquad s_3=-\frac14s_1.
$$

The monic cubic whose roots are the three detunings factors exactly:

$$
x^3-s_1x^2-\frac14x+\frac14s_1
=(x-s_1)(x-\tfrac12)(x+\tfrac12).
$$

Thus the zero set is every permutation of `(a,1/2,-1/2)`. Its squared norm is
`a^2+1/2`, proving the global minimum at `a=0`. Analytic differentiation of
the rational amplitude gives singular values `(sqrt(2),sqrt(2))` there.

## Printed transmission counterexample

On the path in `GOLD_AUDIT.md`, expanding the exact printed rational expression
to the leading nonzero order gives a negative numerator of order
`epsilon^4` over a positive denominator of order `epsilon^8`. This proves a
minus-infinite infimum at `phi=pi/6` without relying on floating-point search.
