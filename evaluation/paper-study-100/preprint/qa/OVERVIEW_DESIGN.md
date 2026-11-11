# Overall reproduction figure contract

Conclusion: the unified 100-paper project contains substantial but uneven recorded claim reproduction, with incomplete measurements and distinct scientific-review maturity.

Archetype: quantitative grid with a wide per-paper distribution as the central panel. Python/matplotlib, 183 mm wide, vector PDF/SVG with editable text, 300 dpi PNG preview. No image generation or manual editing of scientific data. No new case executions.

Panel a gives equal weight to each measured numerical claim. Panel b weights claims within each measured paper and retains every cohort identity. Panel c shows separate assessment dimensions; it is not a funnel. Shared checks are not independent trials. No confidence intervals, significance tests or imputed missing scores are used. All archived supporting claim associations are included, matching the actual source table; its prose description of direct-only mapping is not silently adopted.

Coverage table date: 2026-08-27. Both that historical table and case assessment files are read from the frozen report revision. The figure does not pretend they are one contemporaneous evaluation. Complete recorded claim coverage is not whole-paper acceptance. Missing scores stay blank. Numerical claims absent from the snapshot are not assigned invented denominators.

Sources: anc/overview_summary.json records input hashes; overview_papers.csv, overview_claims.csv and overview_checks.csv contain figure-level source data. build_overview.py checks the claim mapping and rebuilds both weighted summaries. package_arxiv.py validates source-package denominators and missing-value handling.
