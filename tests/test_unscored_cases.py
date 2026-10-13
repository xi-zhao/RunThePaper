import unittest
from scripts.render_case_catalog import audit_label
from scripts.validate_public_cases import validate_scorecard


class UnscoredCases(unittest.TestCase):
    def test_explicitly_unscored_is_not_zero(self):
        validate_scorecard({'audit_score': None}, {
            'overall_score': None, 'score_status': 'not_assessed',
            'reason': 'No calibrated whole-paper score.'})
        self.assertIn('未评分', audit_label(None))
        self.assertEqual('0.00/100', audit_label(0))

    def test_incomplete_unscored_declarations_are_rejected(self):
        for card in ({'overall_score': 0}, {'overall_score': None},
                     {'overall_score': None, 'score_status': 'not_assessed', 'reason': ''}):
            with self.subTest(card=card), self.assertRaises(ValueError):
                validate_scorecard({'audit_score': None}, card)

    def test_existing_numeric_scores_and_mismatch(self):
        validate_scorecard({'audit_score': 78.85}, {'overall_score': 78.85})
        self.assertEqual('78.85/100', audit_label(78.85))
        for score in (79, float('nan'), float('inf'), -1, 101):
            with self.subTest(score=score), self.assertRaises(ValueError):
                validate_scorecard({'audit_score': 78.85}, {'overall_score': score})
