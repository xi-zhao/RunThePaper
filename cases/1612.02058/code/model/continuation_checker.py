"""Bind fresh simulations, distinct controls and original vector/PDF measurements."""
import os
os.environ['MPLCONFIGDIR'] = 'local-source'
from pathlib import Path
from tempfile import TemporaryDirectory
from fractions import Fraction
import json
import shutil
import subprocess
import sys
import fitz
import mpmath as mp

root = Path.cwd()
bundle, generation = sys.argv[1:3]
assets = root / 'review-input/assets'
gen = assets / 'experiments' / generation / 'output/continuation'
out = root / 'continuation/review'
out.mkdir(parents=True, exist_ok=True)
with TemporaryDirectory(prefix='mit-check-', dir=root) as temp:
    work = Path(temp)
    shutil.copytree(gen / 'results', work / 'results')
    shutil.copytree(gen / 'controls', work / 'checks')
    (work / 'code').mkdir()
    (work / 'figures').mkdir()
    for name in ['extract_reference.py', 'bath_consistency_bound.py', 'render.py']:
        shutil.copyfile(root / 'code' / name, work / 'code' / name)
    for name in ['source-fig1.svg', 'source-fig2.svg']:
        shutil.copyfile(assets / 'snapshot/checks' / name, work / 'checks' / name)
    for name in ['extract_reference.py', 'bath_consistency_bound.py', 'render.py']:
        subprocess.run([sys.executable, '-B', 'code/'+name], cwd=work, check=True)
    for p in (work / 'checks').glob('*.json'):
        shutil.copyfile(p, out / p.name)
    for p in (work / 'figures').glob('*.png'):
        shutil.copyfile(p, out / p.name)

read = lambda name: json.loads((out / (name+'.json')).read_text())
ref = read('reference_values')
control = read('numerical_checks')
mp.mp.dps = 80
eps_max = mp.mpf('.001003')
lam_max = -mp.log1p(-eps_max)/2
bound = mp.cosh(12*lam_max)**4-1
source = mp.mpf(str(ref['figure1']['bath'][0]['error'][0]))
lower = source/mp.power(10, mp.mpf('.15'))
uniform = {'epsilon_upper': str(eps_max), 'bound_upper': str(bound),
           'source_center': str(source), 'source_lower_015_decade': str(lower),
           'positive_gap': str(lower-bound), 'excludes_literal_conjunction': bool(lower > bound),
           'reading_envelope': '0.15 decade, not a statistical confidence interval',
           'assumptions': 'N=4,T=12; normalized product Z-diagonal bath; norm-1 system Pauli; absolute error; printed lambda mapping.'}

drawings = fitz.open(assets / 'snapshot/source/extracted/sample_tmp.pdf')[0].get_drawings()
key = lambda rect: tuple(round(x, 3) for x in rect)
filled, stroked = {}, {}
for drawing in drawings:
    rect = drawing['rect']
    if 5.6 < rect.width < 5.9 and abs(rect.y1-159.8886) < .01 and rect.height > .01:
        if drawing['fill'] is not None:
            filled[key(rect)] = rect.height
        elif drawing['color'] == (0.0, 0.0, 0.0):
            stroked[key(rect)] = rect.height
hist = {}
for name, rows in [('off', filled), ('on', {k:v for k,v in stroked.items() if k not in filled})]:
    counts = [v/154.3716*250 for v in rows.values()]
    hist[name] = {'counts': [round(x) for x in counts], 'total': sum(round(x) for x in counts),
                  'integer_residual': max(abs(x-round(x)) for x in counts)}
    assert hist[name]['total'] == ref['figure2'][name]['total_displayed_count']

exact = []
for order in [1, 2, 3]:
    nodes = list(range(1, order+2))
    weights = []
    for c in nodes:
        w = Fraction(1)
        for d in nodes:
            if d != c:
                w *= Fraction(d, d-c)
        weights.append(w)
    moments = [sum(w*c**k for w,c in zip(weights,nodes)) for k in range(order+1)]
    assert moments == [1]+[0]*order
    exact.append({'order': order, 'correct_weights': [str(x) for x in weights],
                  'printed_sum': str(sum(weights)*(-1)**order), 'moments': [str(x) for x in moments]})
summary = {'uniform_bound': uniform, 'direct_pdf_histogram': hist,
           'exact_richardson': exact, 'projector_example': {'top_half': .9, 'argmin_half': .1},
           'physical_scope': 'Printed-condition consistency checks, not identification of author code.'}
(out / 'source_checks.json').write_text(json.dumps(summary, indent=2)+'\n')
D, C, B = 'checks/derivation.md', 'checks/continuation_scope.md', 'checks/bath_consistency_proof.md'
ev = ['continuation/review/'+n+'.json' for n in ['source_checks', 'reference_values',
      'numerical_checks', 'bath_sensitivity', 'grouping_diagnostic', 'bath_consistency_bound']]
findings = []
def add(obj, check, outcome, observation, cause='none'):
    evidence = {'applicability': [D,C,B], 'derivation': [D,C,B],
                'error_analysis': ev, 'independent_check': ev}
    if cause == 'paper_candidate':
        evidence.update({k:[D,C,B]+ev for k in ['implementation_check','parameter_check','information_check']})
    findings.append({'object_id':obj, 'check_id':check, 'outcome':outcome, 'cause':cause,
        'observation':observation,
        'method':'Distinct ODE, dense propagator, Taylor hierarchy, Kraus/branch checks; exact rational algebra and direct PDF geometry versus SVG.',
        'evidence_paths':[D,C,B]+ev,
        'next_action': 'Keep this conditional result and explicit variant boundary.' if outcome=='supports' else
            'Preserve the unresolved original target; obtain source conventions or data without fitting them to the answer.',
        'basis':{'kind':'mixed','experiment_ids':[generation],'evidence':evidence},'resolutions':[]})
for obj, model in [('fig1a','depolarizing'),('fig1b','amp_dephase')]:
    v = control['fig1'][model]
    assert max(v['max_observable_difference'],v['max_extrapolated_difference']) < 2e-10
    add(obj,'instance','supports',f"Explicit independent instance and moment weights; ODE residuals {v['max_observable_difference']}, {v['max_extrapolated_difference']}. Not the unknown original draw.")
    add(obj,'original_curves','inconclusive','Original random controls, graph, Pauli, initial state and scaling nodes are not reported; no pointwise match established.','missing_information')
add('fig1a','literal_generator','discrepancy',f"Printed sign gives minimum eigenvalue {control['literal']['literal_depolarization_min_eigenvalue_t1_lambda001']}; supplement's positive sign is physical and used explicitly.",'paper_candidate')
assert uniform['excludes_literal_conjunction'] and read('bath_consistency_bound')['all_second_through_tenth_points_violate_necessary_bound']
add('fig1c','literal_bound','discrepancy',f"Source n=0 first point lower envelope {lower} exceeds uniform upper bound {bound}; all nine later points also fail the separate finite-range necessary condition. This concerns the conjunction of printed conditions, not Richardson's theorem.",'paper_candidate')
add('fig1c','leading_order','supports',f"Bath diagonal symmetry forces a1=0; Taylor coefficients {control['fig1']['bath']['dyson_coefficients_E0_through_E5']}; first Richardson step amplifies this instance by {control['fig1']['bath']['observed_n1_error_amplification_low_epsilon']}.")
add('fig1c','higher_source_curves','inconclusive','The n=1..3 original curves and author noise convention are not recreated by the explicit literal-model instance.','missing_information')
v = control['fig2']
assert abs(v['mean_bias_z']) < 4 and max(abs(x) for row in v['full_size_crosschecks'] for x in row['differences']) < 2e-12
add('fig2','eq10_instance','supports',f"Fresh 500 six-qubit depth-20 circuits, 4000 shots each: medians {v['median_errors']}, RMSE {v['rmse_off_on']}, improved fraction {v['improved_fraction']}; bias z={v['mean_bias_z']}. Exact one-shot reduction and direct full-size gates cross-checked.")
add('fig2','histogram_count','discrepancy',f"Direct PDF and SVG agree on counts {[hist[k]['total'] for k in ['off','on']]}, not caption 500; residuals {[hist[k]['integer_residual'] for k in ['off','on']]}. No author arrays are available.",'paper_candidate')
add('fig2','grouped_histogram','inconclusive','Our Eq10 choice K=M differs from the unspecified optimized grouping. Three direct full-size QPR samples show K changes variance; no guessed K is substituted.','missing_information')
add('fig2','projector_literal','discrepancy','Supplement argmin selects probability .1 rather than .9 in the normalized four-outcome control; caption/prose specify the largest half. Generation explicitly uses largest half.','paper_candidate')
add('richardson','moment_bound','supports','Exact rational moments and rescaling identity checked; Volterra trace-norm bound rederived for bounded noise unchanged by time rescaling. No unbounded-bath claim.')
add('richardson','printed_weights','discrepancy','Printed closed product changes sign for odd n: constant-function control yields -1 instead of +1. Eq4 moment conditions remain valid.','paper_candidate')
add('richardson','interaction_picture','discrepancy',f"Printed interaction picture changes even noise-free state by {control['literal']['printed_interaction_picture_noise_free_change']}; corrected U-dagger convention residual {control['literal']['correct_interaction_picture_noise_free_change']}.",'paper_candidate')
for k in ['depolarizing_inverse_max_residual','exhaustive_signed_density_residual','joint_estimator_probability_residual']:
    assert control['qpr'][k] < 2e-12
add('qpr','unbiased_overhead','supports','QPR linearity gives unbiased estimator and gamma-squared fixed-confidence shot scaling. Conditional grouped allocation has a separate between-circuit variance; unknown pilot allocation is not certified.')
add('qpr','channels','supports',f"Pauli inverse, unsigned reduction and exhaustive 1024-branch residuals: {control['qpr']}.")
for k in ['inverse_identity_residual','prep_identity_residual','full_cnot_following_layer_residual']:
    assert control['amplitude'][k] < 2e-12
add('amplitude_qpr','basis_no_go','supports','Without preparations, every noisy-unitary affine map has the same nonzero translation; trace preservation forces coefficient sum one, so identity cannot be synthesized.')
add('amplitude_qpr','depth_overhead','supports',f"Inverse/preparation and full CNOT-following-layer maps checked: {control['amplitude']}. Depth preservation requires the stated subsequent single-qubit layer; no generic hardware claim.")
objects = sorted({f['object_id'] for f in findings})
report = {'format':'pragent.research-report.v1','bundle_sha256':bundle,
    'reviewer':{'identity':'Research Agent','context':'same_context',
        'context_evidence':'Same conversation generated and checked; no subagents or external model.',
        'isolation':'No independent-context claim; prior exploratory work was read.'},
    'findings':findings,'object_assessments':[{'object_id':obj,
        'coverage':{'conditions':'adequate','requirements':'adequate','dependencies':'adequate',
            'rationale':'All declared main targets retained; unknown source realization/grouping remain unresolved, not waived.', 'evidence_paths':[D,C,B]+ev},
        'method':{'kind':'independent_implementation','rationale':'Distinct physics/algebra checks beyond replay; original PDF separately measured.','evidence_paths':[D,C,B]+ev},
        'boundary':{'prior_reasoning_exposure':'present','reads':'Fixed v3, existing exploratory code/derivations and fresh frozen output.',
            'limitations':'Same Agent; not a separate researcher, proof assistant or exact hidden-author-code replication.'}} for obj in objects],
    'limitations':'Independent instance is not source-curve agreement; unknown random draws and optimized K remain. Local printed-condition contradictions do not reject error mitigation.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'source_checks':summary,'outcomes':{k:sum(f['outcome']==k for f in findings) for k in ['supports','discrepancy','inconclusive']}},indent=2))
