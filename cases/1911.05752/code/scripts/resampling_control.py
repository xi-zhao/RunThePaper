"""Exact finite control for two count-normalized multinomial resampling stages.

Independent enumerative implementation; no author data/code is imported.
This is a branching-law diagnostic, not an implementation of the full NMQA filter.
"""
from fractions import Fraction as F
from math import comb
from pathlib import Path
import json


def binomial(n, k, p):
    return F(comb(n, k)) * p**k * (1-p)**(n-k)


def distribution(n, p, stages):
    first = [binomial(n, m, p) for m in range(n+1)]
    if stages == 1:
        return first
    return [sum((first[m]*binomial(n, k, F(m, n))
                 for m in range(n+1)), F(0)) for k in range(n+1)]


rows = []
for n in (1, 2, 3, 5, 10):
    for stages in (1, 2):
        probs = distribution(n, F(1, 2), stages)
        mean = sum((F(k)*v for k, v in enumerate(probs)), F(0))
        variance = sum(((F(k)-mean)**2*v for k, v in enumerate(probs)), F(0))
        expected_variance = F(n, 4) * (1 if stages == 1 else 2-F(1,n))
        assert sum(probs) == 1 and mean == F(n,2)
        assert variance == expected_variance
        # q=(0.9,-0.9,-0.9) for n_alpha=3; category 1 against its complement.
        q_covariance_q = F(9,5)**2 * variance
        rows.append({"n": n, "stages": stages,
                     "probabilities": [str(v) for v in probs],
                     "mean": str(mean), "variance": str(variance),
                     "closed_form_variance_residual": str(variance-expected_variance),
                     "q_covariance_q": str(q_covariance_q),
                     "c_equals_one_bound_n": str(n),
                     "exceeds_c1_bound": q_covariance_q > n})

result = {"interpretation": "Two consecutive multinomial draws, each with n offspring; stage-two probabilities are the normalized stage-one counts.",
          "paper_relation": "Control for Section IV branching explanation and Section V c_t=1 inference; exact correspondence to the complete adaptive update still requires audit.",
          "n3_realization": "n_alpha=3, n_beta=2; six pair weights (1/4,1/4,1/8,1/8,1/8,1/8) collapse to parent probabilities (1/2,1/4,1/4).",
          "rows": rows,
          "limits": ["Not a full NMQA numerical reproduction", "No claim about empirical figure slopes from this finite branching control alone", "A changed variance constant does not remove the O(1/n) convergence order"]}
Path("results/resampling_control.json").write_text(json.dumps(result, indent=2)+"\n")
