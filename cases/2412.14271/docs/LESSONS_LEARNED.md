# Lessons learned

1. **A plotted branch must be identified before its spectrum is interpreted.**
   Matching only line style or a nearby root can pair the correct photon number
   with the wrong Jacobian.
2. **A zero Bogoliubov eigenvalue is not automatically stable.** For the lower
   branch plotted in Fig. 3(g), the linear spectrum is marginal, while the
   leading amplitude equation along the photon zero mode has a positive cubic
   coefficient and is therefore nonlinearly unstable.
3. **Scientific and visual gates answer different questions.** Seven numerical
   figure groups have valid generated artifacts, yet the foreground pixel score
   remains 46.71/100 because trajectory counts and rendering differ.
4. **Reduced Monte-Carlo ensembles must stay visibly labeled.** They can verify
   phase structure, parity, and qualitative distributions, but cannot support a
   paper-exact claim.
5. **Blocked targets are better than invented parameters.** Formal supplemental
   Figs. S3–S4 remain outside the claimed coverage until their defining
   parameters can be established.

The branch-specific finding and its limits are recorded in
[PAPER_DISCREPANCY.md](PAPER_DISCREPANCY.md).
