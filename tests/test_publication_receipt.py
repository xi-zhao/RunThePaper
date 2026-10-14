import contextlib
import io
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.verify_publication import verify


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.git('init','-q')
        self.git('config','user.email','test@example.invalid')
        self.git('config','user.name','Test')
        (self.root/'scripts').mkdir()
        for name in ('validate_public_cases.py','render_case_catalog.py'):
            (self.root/'scripts'/name).write_text('print("fixture validator")\n')
        self.git('add','scripts');self.git('commit','-qm','fixture')
        self.sha=self.git('rev-parse','HEAD').strip()

    def git(self,*args):
        return subprocess.check_output(['git',*args],cwd=self.root,text=True)

    def run_receipt(self,expected=None):
        with contextlib.redirect_stdout(io.StringIO()):
            code=verify(self.root,expected or self.sha,self.root/'receipt.json')
        return code,json.loads((self.root/'receipt.json').read_text())

    def test_clean_exact_commit(self):
        code,receipt=self.run_receipt()
        self.assertEqual(0,code);self.assertTrue(receipt['passed'])

    def test_wrong_expected_sha(self):
        code,receipt=self.run_receipt('a'*40)
        self.assertEqual(1,code);self.assertFalse(receipt['passed'])

    def test_untracked_validator_input(self):
        (self.root/'scripts/hidden.py').write_text('x=1')
        code,receipt=self.run_receipt()
        self.assertEqual(1,code)
        self.assertTrue(any('not a regular committed file' in x for x in receipt['errors']))

    def test_assume_unchanged_cannot_hide_modified_validator(self):
        self.git('update-index','--assume-unchanged','scripts/validate_public_cases.py')
        (self.root/'scripts/validate_public_cases.py').write_text('print("modified validator")\n')
        self.assertEqual('',self.git('diff','HEAD'))
        code,receipt=self.run_receipt()
        self.assertEqual(1,code)
        self.assertTrue(any('bytes or mode differ' in x for x in receipt['errors']))

    def test_failed_validator_is_saved_as_failure(self):
        (self.root/'scripts/validate_public_cases.py').write_text('raise SystemExit(1)\n')
        self.git('add','scripts');self.git('commit','-qm','reject')
        code,receipt=self.run_receipt(self.git('rev-parse','HEAD').strip())
        self.assertEqual(1,code);self.assertEqual(1,receipt['validator_exit_code'])


if __name__=='__main__': unittest.main()
