# Derivation used by the reproduction

## Realification arithmetic law

For one fixed contraction tree, normalize the complex skeleton volume to one.
Let `m` be the fraction of volume at merge nodes and `r` the fraction at ride
nodes. The remaining `1-m-r` is pass volume. Realification assigns arithmetic
factors three, two, and one respectively, hence

$$
o = 3m + 2r + (1-m-r) = 1 + 2m + r.
$$

Because `m >= 0`, `r >= 0`, and `m+r <= 1`, eliminating `r` gives

$$
1+2m \le o \le 2+m,
$$

and therefore `1 <= o <= 3`. The implementation evaluates integer pass, ride,
and merge volumes first, then applies this normalized identity; Figure 8 checks
it independently for every generated tree.

Relevant implementation: `code/src/independent_tn.py` (`TreeStatistics`) and
`code/src/realified_figures.py` (`CostLawPoint`).

## Contraction-order transfer gap

Figure 9 compares the overhead of a tree optimized on the skeleton and then
converted, `o_conv`, with a separately optimized realified tree, `o_full`:

$$
g = \frac{|o_{\mathrm{conv}}-o_{\mathrm{full}}|}{o_{\mathrm{full}}}.
$$

The reproduction also records the relative difference of the unnormalized
real arithmetic costs. This second observable prevents a changing per-tree
skeleton denominator from making two genuinely different costs look equal.

Relevant implementation: `code/scripts/run_independent_reimplementation.py`
and `code/src/realified_figures.py` (`PipelinePoint`).
