"""Metadata regression tests only; no research runtimes or case imports."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from validate_plan import validate, validate_repository_source

HERE = Path(__file__).resolve().parent


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((HERE / 'cohort.json').read_text(encoding='utf-8'))
        self.template = json.loads((HERE / 'RESULT_RECORD_TEMPLATE.json').read_text(encoding='utf-8'))

    def test_valid_plan(self):
        result = validate(self.plan, self.template)
        self.assertEqual(result['planned_detailed_cases'], 100)
        self.assertEqual(result['scientific_cases_executed'], 0)

    def test_missing_historical_id(self):
        self.plan['retained_historical_ids'].pop()
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_duplicate_historical_id(self):
        self.plan['retained_historical_ids'][1] = self.plan['retained_historical_ids'][0]
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_replaced_historical_id(self):
        self.plan['retained_historical_ids'][1] = 'fake-paper'
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_deleted_exclusion_reason(self):
        self.plan['excluded_from_detailed_analysis'][0]['reason'] = ''
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_historical_source_drift(self):
        self.plan['historical_source']['commit'] = 'main'
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_duplicate_addition(self):
        self.plan['prospective_additions'][1] = copy.deepcopy(self.plan['prospective_additions'][0])
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_duplicate_doi(self):
        self.plan['prospective_additions'][1]['doi'] = self.plan['prospective_additions'][0]['doi']
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_unversioned_source(self):
        self.plan['prospective_additions'][0]['source_url'] = 'https://arxiv.org/abs/quant-ph/9604005'
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_execution_claim(self):
        self.plan['prospective_additions'][0]['execution_status'] = 'completed'
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_premature_scientific_verdict(self):
        self.plan['prospective_additions'][0]['scientific_verdict'] = 'reproduced'
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_old_case_rerun_enabled(self):
        self.plan['policy']['old_case_scientific_execution_allowed'] = True
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_failures_can_be_replaced(self):
        self.plan['policy']['replace_new_failures_to_reach_success_count'] = True
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_false_result_in_template(self):
        self.template['comparison']['observed_value'] = 1.0
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_wrong_planned_count(self):
        self.plan['planned_detailed_case_count'] = 103
        with self.assertRaises(ValueError): validate(self.plan, self.template)

    def test_modified_repository_csv(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / self.plan['historical_source']['path']
            path.parent.mkdir(parents=True)
            path.write_text('paper_id,title\nfake,Fiction\n', encoding='utf-8')
            with self.assertRaises(ValueError): validate_repository_source(self.plan, Path(temp))


if __name__ == '__main__':
    unittest.main()
