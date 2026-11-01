import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import swag_task_corpus as corpus


class TaskCorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sources = self.root / 'source'
        (self.sources / 'sources').mkdir(parents=True)
        self.reviews = self.root / 'reviews.jsonl'
        rows, reviews = [], []
        for index, project in enumerate(['rrflow/rrflow-development', 'rrflow/connectome-development']):
            raw = {'title': f'Implement distinct task {index}', 'repository': project, 'headRefOid': str(index) * 40}
            data = corpus.canonical_bytes(raw)
            digest = corpus.sha(data)
            (self.sources / 'sources' / (digest + '.json')).write_bytes(data)
            row = {'taskId': project + '#1', 'sourceSha256': digest, 'sourceRevision': raw['headRefOid'],
                   'taskText': raw['title'], 'project': project, 'sourceUrl': 'https://example.test/pr/1'}
            rows.append(row)
            reviews.append({'taskId': row['taskId'], 'sourceSha256': digest,
                            'reviewKind': 'assistant_inferred_intent', 'reviewerId': 'fixture-assistant',
                            'taskFamily': 'implementation', 'rationale': 'Fixture review only'})
        content = b''.join(corpus.canonical_bytes(row) + b'\n' for row in rows)
        (self.sources / 'review-candidates.jsonl').write_bytes(content)
        (self.sources / 'manifest.json').write_bytes(corpus.canonical_bytes({'candidateSha256': corpus.sha(content)}))
        self.reviews.write_text('\n'.join(json.dumps(row) for row in reviews))
        self.output = self.root / 'output'

    def test_project_holdout_and_provisional_status(self):
        manifest = corpus.build(self.sources, self.reviews, self.output)
        self.assertEqual(corpus.verify(self.output), manifest)
        self.assertFalse(manifest['routingDatasetAdmitted'])
        self.assertFalse(manifest['humanReviewed'])
        chats = corpus.lines(self.output / 'train.chat.jsonl')
        self.assertNotIn('sourceUrl', str(chats))
        self.assertNotIn('changedPaths', str(chats))

    def test_changed_source_rejected(self):
        path = next((self.sources / 'sources').glob('*.json'))
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Source evidence changed'):
            corpus.build(self.sources, self.reviews, self.output)
        self.assertFalse(self.output.exists())

    def test_duplicate_review_rejected(self):
        self.reviews.write_text(self.reviews.read_text() + '\n' + self.reviews.read_text().splitlines()[0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            corpus.build(self.sources, self.reviews, self.output)

    def test_changed_export_rejected(self):
        corpus.build(self.sources, self.reviews, self.output)
        with (self.output / 'train.chat.jsonl').open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(ValueError, 'artifact changed'):
            corpus.verify(self.output)

    def test_cannot_claim_human_review_or_qualification(self):
        corpus.build(self.sources, self.reviews, self.output)
        path = self.output / 'manifest.json'
        manifest = json.loads(path.read_text())
        manifest['humanReviewed'] = True
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Invalid provisional'):
            corpus.verify(self.output)


if __name__ == '__main__':
    unittest.main()
