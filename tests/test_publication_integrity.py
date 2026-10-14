import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_public_cases import validate_authority_projection


class NativePublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checks = self.root / 'outputs/checks'
        self.checks.mkdir(parents=True)
        self.case = dict(paper_id='paper', registry_scope='paper_reproduction',
                         authority_mode='native', authoritative_status='unfinished',
                         complete=False, master_git_sha='a'*40)
        self.completion = dict(self.case, assessment_freshness='current', integrity='valid',
                               source_run_id='00000000-0000-0000-0000-000000000001',
                               source_version=2, source_snapshot_sha256='b'*64)
        self.provenance = dict(self.completion, generated_checks=['outputs/checks/completion_assessment.json'], files=[dict(public_path='code.py', transformation='byte-for-byte',
                               source_sha256=hashlib.sha256(b'x=1\n').hexdigest(),
                               public_sha256=hashlib.sha256(b'x=1\n').hexdigest())])
        (self.root/'code.py').write_bytes(b'x=1\n')

    def write(self):
        for name, value in [('completion_assessment', self.completion),
                            ('publication_provenance', self.provenance)]:
            (self.checks/(name+'.json')).write_text(json.dumps(value))
        manifest = dict(format='runthepaper.publication-manifest.v1', paper_id='paper',
                        master_git_sha='a'*40, files={p.relative_to(self.root).as_posix():
                        hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*')
                        if p.is_file() and p.name != 'publication_manifest.json'})
        (self.checks/'publication_manifest.json').write_text(json.dumps(manifest))

    def errors(self):
        errors=[]
        validate_authority_projection(self.case,self.root,errors)
        return errors

    def test_fresh_unfinished_case_is_admissible(self):
        self.write()
        self.assertEqual([],self.errors())

    def test_stale_or_invalid_assessment_is_rejected(self):
        for key,value in [('assessment_freshness','stale'),('integrity','invalid')]:
            with self.subTest(key=key):
                old=self.completion[key]
                self.completion[key]=value
                self.write()
                self.assertTrue(self.errors())
                self.completion[key]=old

    def test_source_binding_mismatches_are_rejected(self):
        for field in ('source_run_id','source_version','source_snapshot_sha256','master_git_sha'):
            with self.subTest(field=field):
                old=self.provenance[field]
                self.provenance[field]=None
                self.write()
                self.assertTrue(self.errors())
                self.provenance[field]=old

    def test_tampered_code_is_rejected(self):
        self.write()
        (self.root/'code.py').write_bytes(b'x=2\n')
        self.assertTrue(any('hash mismatch' in x for x in self.errors()))

    def test_extra_file_is_rejected(self):
        self.write()
        (self.root/'unlisted.py').write_text('x=2')
        self.assertTrue(any('inventory mismatch' in x for x in self.errors()))

    def test_missing_manifest_is_rejected(self):
        self.write()
        (self.checks/'publication_manifest.json').unlink()
        self.assertTrue(self.errors())

    def test_path_escape_is_rejected(self):
        self.write()
        path=self.checks/'publication_manifest.json'
        obj=json.loads(path.read_text());obj['files']['../outside']='a'*64
        path.write_text(json.dumps(obj))
        self.assertTrue(any('unsafe manifest' in x for x in self.errors()))

    def test_changed_lineage_is_rejected(self):
        self.provenance['files'][0]['public_sha256']='c'*64
        self.write()
        self.assertTrue(any('source lineage' in x for x in self.errors()))

    def test_byte_copy_cannot_change_source_hash(self):
        self.provenance['files'][0]['source_sha256']='c'*64
        self.write()
        self.assertTrue(any('byte-for-byte' in x for x in self.errors()))

    def test_manifest_cannot_omit_code_lineage(self):
        (self.root/'extra.py').write_text('x=2')
        self.write()
        self.assertTrue(any('does not cover' in x for x in self.errors()))

    def test_python_in_cache_directory_is_still_checked(self):
        self.write()
        (self.root/'__pycache__').mkdir()
        (self.root/'__pycache__/extra.py').write_text('x=2')
        self.assertTrue(any('inventory mismatch' in x for x in self.errors()))

    def test_removing_mode_does_not_bypass_native_rules(self):
        for item in (self.case,self.completion,self.provenance):
            item.pop('authority_mode')
        self.completion['assessment_freshness']='stale'
        self.write()
        self.assertTrue(any('not current' in x for x in self.errors()))


if __name__ == '__main__':
    unittest.main()
