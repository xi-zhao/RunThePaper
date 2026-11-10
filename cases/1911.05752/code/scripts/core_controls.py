"""Independent scalar controls for arXiv:1911.05752v2.

These are exact algebra/integration diagnostics, not nine-panel NMQA simulation.
No author code or author result arrays are imported.
"""
from fractions import Fraction as F
from math import comb, erf, exp, log, pi, sqrt
from pathlib import Path
import json


def rho(b, variance):
    sigma = sqrt(variance)
    z = 2*b/(sqrt(2)*sigma)
    return erf(z) + (exp(-z*z)-1)/(z*sqrt(pi))


def convolved_density(v, b, variance):
    denom = sqrt(2*variance)
    return (erf((v+b)/denom)-erf((v-b)/denom))/(4*b)


def simpson(fn, a, b, intervals):
    h = (b-a)/intervals
    return h/3*(fn(a)+fn(b)+sum((4 if k % 2 else 2)*fn(a+k*h)
                              for k in range(1, intervals)))


rows = []
for b, variance in [(0.5,0.01),(0.5,0.77),(0.5,1.0),(0.5,10.0)]:
    analytic = rho(b, variance)
    integral = simpson(lambda v: convolved_density(v,b,variance), -b,b,4096)
    finer = simpson(lambda v: convolved_density(v,b,variance), -b,b,8192)
    assert abs(analytic-finer)<1e-10 and abs(integral-finer)<1e-10
    rows.append(dict(b=b,variance=variance,rho=analytic,
                     integrated_truncated_mass=finer,
                     analytic_integral_difference=analytic-finer,
                     mesh_refinement_difference=integral-finer,
                     outcome_probability_sum=analytic))

prior=[F(1,6),F(1,3),F(1,2)]
born=[F(1,4),F(1,2),F(3,4)]
weights=[]
for scale in [F(1,10),F(1,2),F(9,10),F(1)]:
    raw=[a*p*scale for a,p in zip(prior,born)]
    weights.append([v/sum(raw) for v in raw])
assert all(w==weights[0] for w in weights)

# A finite exact posterior control: binary hidden probability, five measurements.
# It illustrates the difference between approximation error and true-field MSE.
truth=F(4,5); alternatives=[F(1,5),F(4,5)]; trials=5
bias_floor=F(0); posterior_variance=F(0)
for k in range(trials+1):
    data_probability=F(comb(trials,k))*truth**k*(1-truth)**(trials-k)
    likelihoods=[p**k*(1-p)**(trials-k) for p in alternatives]
    posterior=[v/sum(likelihoods) for v in likelihoods]
    mean=sum(a*p for a,p in zip(posterior,alternatives))
    variance=sum(a*(p-mean)**2 for a,p in zip(posterior,alternatives))
    bias_floor += data_probability*(mean-truth)**2
    posterior_variance += data_probability*variance
risk=[]
for n in [3,9,15,21,30,300,3000]:
    risk.append(dict(n=n,bayes_bias_floor=str(bias_floor),
                     particle_approximation_mse=str(posterior_variance/n),
                     true_field_mse=str(bias_floor+posterior_variance/n)))

# Literal printed recursive equation, as opposed to a running-mean correction.
kappa0=F(1)
y1=F(1)
tau1=1
kappa1=kappa0+y1/tau1
inverse_cos_argument=2*kappa1-1
assert inverse_cos_argument>1

# Boundary of lambda**tau and the unmeasured-site branch of H.
no_sharing = dict(lambda1=0,lambda2=0,tau=0,phi=1,
                  lambda2_power_tau=1,
                  H_branch="gamma, independent of lambda1 when tau=0 and phi>0",
                  qualification="A separate explicit zero-sharing guard could define a corrected algorithm; it is not specified in these printed branches.")

result=dict(
 format="qctrl1911.core-controls.v1",
 scope="Bounded diagnostics; no full adaptive filter or original figure reproduction.",
 likelihood=dict(rows=rows,normalized_posterior_weights=[[str(x) for x in w] for w in weights],
                 scale_cancellation_exact=True,
                 full_real_line_convolution_mass=1,
                 note="rho is a truncated mass; the common positive factor cancels in a normalized Bayesian update."),
 error_scaling=dict(trials=trials,truth=str(truth),prior="equal mass at 1/5 and 4/5",
                    bayes_bias_floor=str(bias_floor),posterior_variance=str(posterior_variance),
                    rows=risk,
                    limitation="A declared diagnostic model, not a fitted NMQA figure."),
 update=dict(kappa0=str(kappa0),y1=str(y1),tau1=tau1,
             literal_kappa1=str(kappa1),inverse_cos_argument=str(inverse_cos_argument),
             domain_violation=True,
             limitation="Counterexample to the printed recursion; the empirical-mean prose and author code implement a different update."),
 no_sharing=no_sharing)
Path("results/core_controls.json").write_text(json.dumps(result,indent=2)+"\n")
