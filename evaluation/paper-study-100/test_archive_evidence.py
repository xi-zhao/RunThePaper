"""Scientific interpretation boundaries of the read-only archive extraction."""
import json
from pathlib import Path
import tempfile
import shutil
import subprocess
import sys
import unittest
from build_archive_evidence import resolve_reference, scale_relation, write_outputs
from validate_archive_evidence import validate_product
HERE=Path(__file__).resolve().parent

class ArchiveEvidenceTests(unittest.TestCase):
    def test_generated_product_consistency(self):
        self.assertEqual(validate_product()['papers'],97)

    def test_public_projection_mapping(self):
        blobs={'cases/p/code/scripts/run.py':'abc','cases/p/outputs/data/x.csv':'def'}
        self.assertEqual(resolve_reference('cases/p','workspace/scripts/run.py::main',blobs),'cases/p/code/scripts/run.py')
        self.assertEqual(resolve_reference('cases/p','outputs/data/x.csv#column',blobs),'cases/p/outputs/data/x.csv')

    def test_missing_private_receipt_is_not_fabricated(self):
        self.assertIsNone(resolve_reference('cases/p','outputs/runs/run1/run_attestation.json',{}))

    def test_reference_escape_is_rejected(self):
        for reference in ['../other/file.json','/private/file.json','workspace/../../secret']:
            with self.subTest(reference=reference):
                self.assertIsNone(resolve_reference('cases/p',reference,{}))

    def test_unknown_condition_stays_unknown(self):
        for value in [None,'not_recorded','not_applicable','paper_exact_unverified']:
            self.assertEqual(scale_relation(value),'unknown')

    def test_unmapped_targets_remain_visible_and_uncounted(self):
        rows=[json.loads(x) for x in (HERE/'data/results.jsonl').read_text().splitlines()]
        unmapped=[r for r in rows if r['record_origin']=='unmapped_archived_target']
        self.assertTrue(unmapped)
        self.assertTrue(all(not r['count_as_independent_result'] for r in unmapped))
        self.assertTrue(all(r['archived_targets'] for r in unmapped))

    def test_archived_passing_labels_never_become_new_acceptance(self):
        rows=[json.loads(x) for x in (HERE/'data/results.jsonl').read_text().splitlines()]
        exact=[r for r in rows if any(t['archived_parameter_match']=='paper_exact' for t in r['archived_targets'])]
        self.assertTrue(exact)
        self.assertTrue(all(r['review']['outcome']=='not_evaluated' and r['actual_conditions']['scale_relation']=='unknown' for r in exact))

    def test_forged_acceptance_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            shutil.copytree(HERE/'data',root/'data')
            shutil.copyfile(HERE/'cohort.json',root/'cohort.json')
            path=root/'data/results.jsonl'; rows=path.read_text().splitlines()
            row=json.loads(rows[0]); row['review']['outcome']='supported'; rows[0]=json.dumps(row)
            path.write_text('\n'.join(rows)+'\n')
            with self.assertRaisesRegex(ValueError,'promoted'):
                validate_product(root)
    def test_optimized_python_keeps_validation(self):
        code="from validate_archive_evidence import require; require(False, 'intentional_invalid')"
        result=subprocess.run([sys.executable,'-O','-c',code],cwd=HERE,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('intentional_invalid',result.stderr)
    def test_selection_is_exactly_the_fixed_historical_group(self):
        plan=json.loads((HERE/'cohort.json').read_text())
        rows=[json.loads(x) for x in (HERE/'data/papers.jsonl').read_text().splitlines()]
        self.assertEqual({r['paper_id'] for r in rows},set(plan['retained_historical_ids']))
        self.assertTrue(all(r['model'] is None and r['human_interventions'] is None for r in rows))

if __name__=='__main__':
    unittest.main()
