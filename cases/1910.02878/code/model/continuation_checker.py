"""Check a frozen native generation against fixed-v4 sources in the same context."""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import contextlib
import io
import json
from pathlib import Path
import runpy
import shutil
import sys
from tempfile import TemporaryDirectory
import numpy as np
from scipy.optimize import linear_sum_assignment

ROOT = Path.cwd()
BUNDLE, EXPERIMENT = sys.argv[1:3]
SOURCE = ROOT / "review-input/assets/snapshot"
GEN = ROOT / f"review-input/assets/experiments/{EXPERIMENT}/output/continuation"
OUT = ROOT / "continuation/review"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "code"))
with TemporaryDirectory(prefix="skin-check-", dir=ROOT) as tmp:
    tmp = Path(tmp)
    shutil.copytree(GEN / "results", tmp / "results")
    (tmp / "checks").mkdir()
    (tmp / "source/extracted").mkdir(parents=True)
    for f in ("fig2.eps", "NH-SSH.eps", "supp.eps"):
        shutil.copyfile(SOURCE / "source/extracted" / f, tmp / "source/extracted" / f)
    os.chdir(tmp)
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(ROOT / "code/independent_checks.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "code/compare_reference.py"), run_name="__main__")
        from compare_reference import circles
        for name, source in (("ssh", "NH-SSH.eps"), ("s3", "supp.eps")):
            Path(f"checks/{name}_reference_markers.json").write_text(json.dumps({"markers":circles("source/extracted/"+source)},indent=2)+"\n")
        runpy.run_path(str(ROOT / "code/compare_supplement.py"), run_name="__main__")
        runpy.run_path(str(ROOT / "code/diagnose_reference_geometry.py"), run_name="__main__")
    ref = np.loadtxt("checks/fig2a_broken_residuals.csv", delimiter=",", skiprows=1)
    ref = ref[:,0]+1j*ref[:,1]
    variants = {}
    for name, e in np.load("results/diagnostic_variants.npz").items():
        distance = abs(ref[:,None]-e[None,:]);i,j=linear_sum_assignment(distance)
        err=distance[i,j]
        variants[name]={"RMSE":float(np.sqrt(np.mean(err**2))),"max_error":float(err.max())}
    Path("checks/variant_reference_comparison.json").write_text(json.dumps(variants,indent=2)+"\n")
    for p in (tmp / "checks").iterdir():
        shutil.copyfile(p, OUT / p.name)
    os.chdir(ROOT)

read=lambda name:json.loads((OUT/name).read_text())
g=json.loads((GEN/"results/generation.json").read_text())
ic=read("independent_checks.json"); ref=read("reference_comparison.json")
sup=read("supplement_comparison.json"); quant=read("reference_geometry_diagnosis.json")
variants=read("variant_reference_comparison.json")
diagnostic=json.loads((GEN/"checks/diagnostic_variants.json").read_text())
findings=[]
D="checks/DERIVATION.md";C="checks/continuation_scope.md"
I="continuation/review/independent_checks.json";R="continuation/review/reference_comparison.json"
S="continuation/review/supplement_comparison.json";Q="continuation/review/reference_geometry_diagnosis.json"
V="continuation/review/variant_reference_comparison.json"


def add(obj,check,observation,passed=True,*,analytic=False,outcome=None,cause="none",next_action=None):
    ev={"applicability":[D,C],"derivation":[D,C],"error_analysis":[I,R,S,Q,V],"independent_check":[I,D,R,S,V]}
    if cause=="paper_candidate":ev.update(implementation_check=[I,D,V],parameter_check=[D,R,S],information_check=[D,C,Q])
    findings.append({"object_id":obj,"check_id":check,"observation":observation,"outcome":outcome or ("supports" if passed else "inconclusive"),
      "cause":cause,"method":"Distinct analytic channel/recurrence/symmetry arguments and actual numeric source comparisons, with original and variant conditions separated.",
      "evidence_paths":[D,C,I,R,S,Q,V],"next_action":next_action or "Retain this precise scope and the original model; no blanket paper verdict or independent-review claim.",
      "basis":{"kind":"analytic" if analytic else "mixed","experiment_ids":[] if analytic else [EXPERIMENT],"evidence":ev},"resolutions":[]})

add("TI","scalar_index","Scalar finite-range Toeplitz winding/index and zero-index invertibility yield the stated spectrum; explicit decaying quadratic-root solutions and Hermitian/inside/outside controls verify applicability.",analytic=True)
mb=ic["multiband_winding_cancellation"]
add("TI","finite_band_scope",f"Original Eq.(10) has opposite channel indices and total W=0, yet an exact analytic half-line kernel at E=0.2i; its N=160 truncated residual is {mb['SIBC_residuals'][-1]['residual']:.6g}. Bulk [H,Hdagger] norm {mb['bulk_commutator_norm_at_pi_over_2']:.6g} also invalidates the unrestricted essential-normality premise. Scalar theorem and nonzero-index sufficient guarantee survive.",analytic=True,outcome="discrepancy",cause="paper_candidate")
add("TII","proof_scope","Scalar Laurent-root and source-model results support the skin mechanism, but total determinant index does not provide the asserted full multiband spectral equality. The general proof needs a treatment of partial indices/special blocks; no universal counterexample to the skin implication is claimed.",analytic=True,outcome="inconclusive",cause="unknown",next_action="Complete the multiband/general-symmetry argument under the actual source assumptions, rather than infer it from scalar invertibility.")
add("F1a","schematic","Nonzero winding supports the indicated semi-infinite left/right boundary modes; schematic axes and areas are conceptual, not digitized numerical data.",analytic=True)
add("F1b","schematic","For the illustrated scalar HN regime t>|g| the imaginary gauge contracts the periodic ellipse to the finite-open sine spectrum; semi-infinite gauges need not be bounded invertible maps.",analytic=True)
for name in ("pbc","obc","stack"):
    x=ref["fig2a"][name]
    add("F2a",name,f"All {x['reference_count']} source vector markers with multiplicity compared: RMSE {x['RMSE']:.6g}, max {x['max_error']:.6g}, unchanged energy reading bound {ref['energy_error_bound']:.6g}.",x["within_reading_bound"])
x=ref["fig2a"]["broken"]
add("F2a","broken_literal",f"Literal 0.001 sigma_z perturbation differs from all 200 black source markers: RMSE {x['RMSE']:.6g}, max {x['max_error']:.6g}. Sign and spin-major controls retain it; residual-times-condition estimate {diagnostic['z']['max_first_order_residual_times_condition']:.3g} is far smaller.",outcome="discrepancy",cause="paper_candidate")
add("F2a","x_variant",f"Explicit sigma_x variant has RMSE {variants['x']['RMSE']:.6g}, max {variants['x']['max_error']:.6g}; sigma_y and literal sigma_z controls fail. No inference about author code, and no substitution in the literal model.",variants["x"]["max_error"]<ref["energy_error_bound"])
add("F2b","density",f"Both 100-site density traces match the fixed source reading bound; E={g['F2']['doublet_E']:.12g}, peak={g['F2']['doublet_peak']:.12g} at site {g['F2']['doublet_peak_site']}, physical-matrix residual {g['F2']['doublet_residual']:.3g}.",all(x["within_reading_bound"] for x in ref["fig2b"].values()))
add("HN","finite_spectrum","Exact finite spectrum 2 sqrt(t^2-g^2) cos(m*pi/(N+1)) agrees with direct small matrices, including both signs of g and a Hermitian control.",max(x["spectrum_formula_error"] for x in ic["HN_limits"])<1e-10)
add("HN","printed_S24",f"The printed root's missing factor four gives polynomial residual {g['S24']['printed_polynomial_residual']:.6g} at t=1,g=-0.3,E=.2+.1i; 80-digit calculation and the root-product identity confirm it.",analytic=True,outcome="discrepancy",cause="paper_candidate")
add("HN","corrected_S24","The explicitly corrected quadratic root satisfies the recurrence and inside/outside controls to 80-digit precision; this does not retroactively alter the printed formula.",max(float(x["max_polynomial_residual"]) for x in ic["S24_high_precision"] if x["variant"]=="quadratic_corrected")<1e-70,analytic=True)
add("HN","real_spectrum_scope",f"The unrestricted main-text real-spectrum wording needs t>|g| (as stated in the supplement): t=1,g=2,N=12 gives max |Im E|={ic['HN_limits'][-1]['max_abs_ImE']:.12g}. Skin sensitivity itself persists.",analytic=True,outcome="discrepancy",cause="paper_candidate")
add("Z2","index","Pfaffian endpoint formula with continuous logarithm yields nu=1 for the three interior reference energies and zero for two exterior points, while determinant W=0; doubled-Hermitian and transpose-TR algebra independently agree.",all(x["nu"]==n for x,n in zip(g["Z2"],[1,1,0,0,1])) and g["reciprocity_error"]<1e-12)
add("Z2","response","N=50,100,200 controls show unperturbed edge IPR approaching a nonzero limit while stacked and symmetry-broken median IPR decrease. Finite N=100 edge enhancement is not confused with a thermodynamic skin effect.",g["finite_size"][-1]["stack"]["median_IPR"]<g["finite_size"][0]["stack"]["median_IPR"] and g["finite_size"][-1]["broken"]["median_IPR"]<g["finite_size"][0]["broken"]["median_IPR"])
add("LINE","coexistence","Both SSH cases retain an open imaginary-axis line gap and boundary modes together with skin spectra. Distinct bond similarity agrees with generation; 110/160-digit recurrences retain finite splitting rather than declaring exact finite zero.",max(x["spin_major_balanced_to_generation_max"] for x in ic["SSH"])<1e-10)
for panel in ("a","c"):
    x=sup["SSH"][panel]
    add("S2"+panel,"curve",f"All {x['vertex_count']} periodic source path vertices satisfy the independently reconstructed ellipse: max energy distance {x['distance_to_analytic_curve_max']:.6g}; unchanged reading bound {x['vector_reading_bound']:.6g}.",x["distance_to_analytic_curve_max"]<x["vector_reading_bound"])
for panel in ("b","d"):
    x=quant[panel]
    add("S2"+panel,"display_curve",f"Raw fine-grid comparison fails and remains recorded. Source-only post-discovery 0.77238-pt display lattice explains all 200 markers within its half-grid envelope; {x['original_model']['rounded_marker_multiset_matches']} rounded cells match. v+0.01 fails the same bound. This is graphical, not hidden-array, agreement.",x["original_model"]["all_within_bound"] and not x["v_plus_0p01_control"]["all_within_bound"])
alg=max(max(float(v) for k,v in x.items() if k.endswith('error')) for x in ic["doubling_algebra"])
add("D","algebra_continuity",f"Doubled Hermitian spectrum equals +/- singular values and symmetry relations hold, max residual {alg:.3g}; original class-D line-to-point map preserves its Z2 class. This checks the stated semi-infinite continuity argument, not a new superconducting model or exact finite-length zero.",alg<1e-12,analytic=True)
add("HD","count","Analytic kx=0/pi channel decomposition gives 4L modes for even L and 2L for odd L: 80/800 at L=20 and 38/722 at L=19. Generic kx uses coupled reciprocal root pairs, not an arbitrary IPR cutoff.",analytic=True)
add("HD","printed_S75",f"Printed S75 differs by {g['2D']['printed_S75_directed_error']:.6g} from its special source-model subspace: it omits Gamma in the imaginary offset and uses periodic rather than open sine quantization.",analytic=True,outcome="discrepancy",cause="paper_candidate")
add("HD","corrected_S75",f"The separate corrected expression sqrt(1-Gamma^2) cos(m*pi/(L+1)) +/- i*Gamma agrees to {g['2D']['corrected_spectrum_error']:.3g}. It describes the special kx blocks, not the entire cylinder spectrum.",g["2D"]["corrected_spectrum_error"]<1e-10)
add("S3a","spectra","All visible source PBC, cylinder and fully open markers match their fixed vector-reading bound. All 800 generated states are retained; the source crops 36 PBC and 8 cylinder markers outside its plotting range.",all(sup["S3a"][k]["within_reading_bound"] for k in ["pbc2","cylinder","full2"]))
add("CLASS","framework","Forgetting line gaps and quotienting by the generated image subgroup agrees with the representative source entries. Literal Im(fr) union Im(fi) is not necessarily a subgroup: original AIII/S- example has (1,1)+(1,-1)=(2,0) outside the union. The sum subgroup has index two, agreeing with the source Z2 entry; this is a notation/definition defect, not a rederivation or rejection of all 38 classes.",analytic=True,outcome="discrepancy",cause="paper_candidate")
assessments=[{"object_id":o,"coverage":{"conditions":"adequate","requirements":"adequate","dependencies":"adequate","rationale":"All selected original checks addressed; general proof unresolved, literal discrepancies and explicit variants kept separate.","evidence_paths":[D,C,I,R,S,Q,V]},"method":{"kind":"independent_implementation","rationale":"Separate channel/block/recurrence and symmetry reasoning plus direct source coordinate comparison where numerical.","evidence_paths":[D,I,R,S,V]},"boundary":{"prior_reasoning_exposure":"present","reads":"Fixed source and prior derivation/diagnosis, then new frozen generation and actual comparison.","limitations":"Same Agent/context; no independent review, universal-theorem proof, or full classification-table reconstruction."}} for o in sorted({x['object_id'] for x in findings})]
report={"format":"pragent.research-report.v1","bundle_sha256":BUNDLE,"reviewer":{"identity":"Research Agent","context":"same_context","context_evidence":"Current conversation continued its own evidence without subagents or model delegation.","isolation":"No separate-context or OS-isolation claim."},"findings":findings,"object_assessments":assessments,"limitations":"Fixed v4. Local source differences do not negate the core skin mechanism; Theorem II general proof remains unfinished."}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"findings":len(findings),"outcomes":{k:sum(x['outcome']==k for x in findings) for k in ['supports','discrepancy','inconclusive']}},indent=2))
