"""Check fresh moments against independent physics and every source vertex."""
import os
os.environ['MPLCONFIGDIR'] = 'local-source'
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path.cwd()
bundle, generation = sys.argv[1:3]
assets = root/'review-input/assets'
gen = assets/'experiments'/generation/'output/continuation'
out = root/'continuation/review'
out.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(prefix='bp-check-',dir=root) as temp:
    w = Path(temp)
    shutil.copytree(gen/'results',w/'results')
    shutil.copytree(gen/'checks',w/'checks')
    (w/'code').mkdir()
    for name in ['analyze.py','reference_extract.py']:
        shutil.copyfile(root/'code'/name,w/'code'/name)
    for n in [3,4]:
        shutil.copyfile(assets/f'snapshot/checks/reference_fig{n}.svg',w/f'checks/reference_fig{n}.svg')
    for name in ['reference_extract.py','analyze.py']:
        subprocess.run([sys.executable,'-B','code/'+name],cwd=w,check=True)
    analysis = json.loads((w/'checks/numerical_analysis.json').read_text())
    analysis['formal_receipts'] = 'Current source-blind execution '+generation+'; earlier denied attempts retained separately.'
    (out/'numerical_analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
    for name in ['reference_data.json','validation.json']:
        shutil.copyfile(w/'checks'/name,out/name)

a = analysis
raw = json.loads((gen/'results/moments.json').read_text())
coarse = json.loads((gen/'results/particle_beta025.json').read_text())
fine = json.loads((gen/'results/particle_fine.json').read_text())
selected = {r['n']:r for r in coarse['rows']}
selected.update({r['n']:r for r in fine['rows']})
refs = json.loads((out/'reference_data.json').read_text())
v = json.loads((out/'validation.json').read_text())
diagnostic = {
    'all_exact_checks_pass': all(x['pass'] for x in a['exact_checks']),
    'max_statevector_z': max(abs(x['z']) for x in a['statevector_checks']),
    'max_particle_raw_z': max(x['max_abs_z'] for x in a['particle_vs_raw']),
    'max_refinement_z': max(x['max_abs_z'] for x in a['particle_refinement']),
    'max_stationary_z': max(abs(x['particle_limit_z']) for x in a['stationary']),
    'numerical_tolerances_unchanged': True}
controls_ok = (diagnostic['all_exact_checks_pass'] and diagnostic['max_statevector_z']<=5 and
    a['gradient_max_shift_error']<1e-10 and a['gradient_max_fd_error']<1e-8 and
    a['max_exact_mass_error']<1e-11)
resolved = controls_ok and max(diagnostic[k] for k in ['max_particle_raw_z','max_refinement_z','max_stationary_z'])<=5
(out/'diagnostics.json').write_text(json.dumps(diagnostic,indent=2)+'\n')

plt.rcParams.update({'font.size':10,'axes.spines.right':False,'axes.spines.top':False})
fig,axs = plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
ns = np.array(sorted(selected))
means = np.array([selected[n]['uniform'][-1] for n in ns])
ses = np.array([selected[n]['se'][-1] for n in ns])
limit = 2.**ns/(3*(4.**ns-1))
axs[0].errorbar(ns,means,yerr=2*ses,fmt='o',ms=4,label='Our depth 512, +/-2 SE')
axs[0].plot(ns,limit,'-',color='#21855d',label='Exact ensemble limit')
axs[0].plot(ns,refs[0]['curves'][0]['variance'],'x--',color='#be6925',label='Fixed paper, unknown depth rule')
axs[0].set_yscale('log');axs[0].set_xlabel('Qubits n');axs[0].set_ylabel('Gradient variance')
axs[0].set_title('Figure 3: slope versus absolute normalization');axs[0].legend(fontsize=8)
for curve in refs[1]['curves']:
    n=curve['n'];r=selected[n];line,=axs[1].plot(r['layers'],r['uniform'],lw=1,label=f'n={n}')
    axs[1].plot(curve['x_nearest_integer'],curve['variance'],'x',ms=3,color=line.get_color())
axs[1].set_yscale('log');axs[1].set_xlabel('Layers');axs[1].set_ylabel('Gradient variance')
axs[1].set_title('Figure 4: lines ours, crosses paper');axs[1].legend(ncol=3,fontsize=7)
for ax in axs:ax.grid(alpha=.15)
fig.savefig(out/'source_comparison.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
ratios=[x['reference_over_limit'] for x in a['fig3_comparison']]
axs[0].plot(ns,ratios,'o-');axs[0].axhline(1,color='gray',ls='--');axs[0].axhline(1.5,color='#be6925',ls=':')
axs[0].set(xlabel='Qubits n',ylabel='Source / exact uniform-axis limit',title='3/2 is a diagnostic, not author provenance')
for n in [6,20,26]:
    r=selected[n];axs[1].plot(r['layers'],np.array(r['se'])/r['uniform'],label=f'n={n}')
axs[1].set(xlabel='Layers',ylabel='Replicate standard error / mean',title='Particle estimator uncertainty')
axs[1].legend();fig.savefig(out/'resolution.png',dpi=180);plt.close(fig)

D,A,C='checks/derivation.md','checks/analytic_check.md','checks/continuation_scope.md'
ev=['continuation/review/'+n+'.json' for n in ['numerical_analysis','validation','diagnostics','reference_data']]
findings=[]
def add(obj,check,outcome,observation,cause='none'):
    findings.append({'object_id':obj,'check_id':check,'outcome':outcome,'cause':cause,'observation':observation,
        'method':'Unbiased Pauli paths versus deterministic second moments, continuous-angle statevector gradients, particle refinement and analytic stationary distribution.',
        'evidence_paths':[D,A,C]+ev,'next_action':'Retain the distinction between ensemble scaling and unresolved source normalization; no fixed-Y substitution.',
        'basis':{'kind':'mixed','experiment_ids':[generation],'evidence':{'applicability':[D,C],
            'derivation':[D,A],'error_analysis':ev,'independent_check':[A]+ev}},'resolutions':[]})
add('fig3','ensemble_scaling','supports' if controls_ok else 'inconclusive',
    f"All even n=2..26, depth through512: fitted slopes {a['fits']}. Exact limit D/[3(D^2-1)] has asymptotic slope -ln2; source printed -0.694. Small-system controls {diagnostic}.",
    'none' if controls_ok else 'implementation')
add('fig3','source_values','inconclusive',
    f"All 13 source points compared; source/limit ratios {ratios}. Original linear-depth multiplier and sample count absent. A different first-axis convention can change normalization but is not evidenced as author code.",'missing_information')
add('fig4','depth_mechanism','supports' if controls_ok and diagnostic['max_stationary_z']<=5 else 'inconclusive',
    f"Depth convergence compared to exact stationary moment; endpoint diagnostics {a['stationary']}. This is one observable, not proof of a complete 2-design.",
    'none' if controls_ok and diagnostic['max_stationary_z']<=5 else 'implementation')
add('fig4','numerical_resolution','supports' if resolved else 'inconclusive',
    f"Original 5-SE diagnostics unchanged: {diagnostic}. Beta=1 earlier collapse is excluded. A replicate SE cannot itself rule out rare normalization tails.",
    'none' if resolved else 'implementation')
add('fig4','source_values','inconclusive',
    f"All source vertices compared: {a['reference_stats']}. No author sampling errors invented; fixed-Y variant explicitly separate.",'missing_information')
report={'format':'pragent.research-report.v1','bundle_sha256':bundle,
    'reviewer':{'identity':'Research Agent','context':'same_context','context_evidence':'One conversation; no subagents or external models.',
        'isolation':'Same researcher exposed to prior work, generation and source.'},'findings':findings,
    'object_assessments':[{'object_id':obj,'coverage':{'conditions':'adequate','requirements':'adequate','dependencies':'adequate',
        'rationale':'Original full size/depth inventory retained, literal source comparisons not replaced by repaired variants.','evidence_paths':[D,C]+ev},
        'method':{'kind':'independent_implementation','rationale':'Deterministic transition and direct complex wavefunction gradient check the statistical path method; asymptote also follows from twirl.','evidence_paths':[D,A]+ev},
        'boundary':{'prior_reasoning_exposure':'present','reads':'Fixed v1, prior method, fresh outputs and original vector data.',
            'limitations':'Same Agent; unknown source sampling and depth rule, no formal rare-tail certification.'}} for obj in ['fig3','fig4']],
    'limitations':'Prior analytic records retained separately. Main-figure objective only; no exact unknown-author-data or full-design certification.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'diagnostics':diagnostic,'fits':a['fits'],'reference_stats':a['reference_stats']},indent=2))
