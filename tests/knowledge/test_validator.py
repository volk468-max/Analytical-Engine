import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('knowledge_validator', ROOT/'scripts/validate_project_knowledge.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class KnowledgeChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT/v.K, self.root/v.K)
        reports = ROOT/'reports'
        if reports.exists():
            shutil.copytree(reports, self.root/'reports')
        self.override = patch.object(v, 'ROOT', self.root)
        self.override.start()

    def tearDown(self):
        self.override.stop()
        self.tmp.cleanup()

    def mutate(self, file, fn):
        p = self.root/v.K/file
        data = json.loads(p.read_text())
        fn(data)
        p.write_text(json.dumps(data))

    def test_valid_offline(self):
        self.assertEqual(v.validate(), [])

    def test_wrong_sha(self):
        self.mutate('research.json', lambda d: d['records'][0].update(sha='abc'))
        self.assertTrue(any('invalid sha' in e for e in v.validate()))

    def test_status_contradiction(self):
        self.mutate('status.json', lambda d: d['pull_requests'][0].update(merged=True))
        self.assertTrue(any('contradiction' in e for e in v.validate()))

    def test_missing_card(self):
        (self.root/v.K/'research/R01-v1.md').unlink()
        self.assertTrue(any('card missing' in e for e in v.validate()))

    def test_stale_live_pr(self):
        m = json.loads((self.root/v.K/'research.json').read_text())
        st = json.loads((self.root/v.K/'status.json').read_text())
        def fetch(path):
            if path.startswith('pulls/'):
                p = next(p for p in st['pull_requests'] if p['number'] == int(path.split('/')[1]))
                return dict(p, draft=not p['draft'], head={'sha':p['head_sha']})
            if path == 'branches/main':
                return {'commit': {'sha':m['baseline_sha']}}
            if path.startswith('commits/'):
                return {'sha':path.split('/')[1]}
            if path.startswith('git/'):
                return {'sha':path.rsplit('/', 1)[1]}
            r = next(r for r in m['records'] if r['report_path'] in path)
            return {'sha':r['report_blob']}
        self.assertTrue(any('stale draft' in e for e in v.validate(True, fetch=fetch)))

    def test_historical_result_cannot_be_replaced(self):
        original = (self.root/v.K/'research.json').read_text()
        self.mutate('research.json', lambda d: d['records'][0].update(results='replacement'))
        def git(*args):
            if args[0] == 'ls-tree':
                return str(v.K/'research.json')
            if args[0] == 'show':
                return original
            return ''
        with patch.object(v, 'git', git):
            self.assertTrue(any('historical record changed' in e for e in v.validate(base_ref='a'*40)))

    def test_secret_pattern(self):
        with (self.root/v.K/'OPEN_QUESTIONS.md').open('a') as f:
            f.write('\n' + 'ghp_' + 'x'*30)
        self.assertTrue(any('possible secret' in e for e in v.validate()))

    def test_broken_local_source_link(self):
        with (self.root/v.K/'OPEN_QUESTIONS.md').open('a') as f:
            f.write('\n[missing](does-not-exist.md)')
        self.assertTrue(any('broken local link' in e for e in v.validate()))

    def test_unavailable_github_is_not_success(self):
        def unavailable(path):
            raise ValueError('GitHub unavailable')
        with self.assertRaises(ValueError):
            v.validate(True, fetch=unavailable)


if __name__ == '__main__':
    unittest.main()
