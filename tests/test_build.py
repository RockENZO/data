import csv
import json
from pathlib import Path
import tempfile
import unittest
from build_dataset import build, audit

class BuildTests(unittest.TestCase):
    def fixture(self, root, rows):
        path = root / 'input.csv'
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['text', 'binary_label', 'detailed_category', 'data_type', 'dataset', 'source_file'])
            writer.writeheader()
            for text, label, category in rows:
                writer.writerow(dict(text=text, binary_label=label, detailed_category=category, data_type='email', dataset='fixture', source_file='/Users/old/data/source.csv'))
        return path

    def test_reproducible_build_and_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.fixture(root, [('Hello', '0', 'legitimate'), ('Scam', '1', 'phishing'), ('', '1', 'phishing'), ('Hello', '0', 'legitimate')])
            a, b = build(source, root/'a'), build(source, root/'b')
            self.assertEqual(a, b)
            self.assertEqual((a['total_samples'], a['empty_rows_removed'], a['exact_duplicates_removed']), (2, 1, 1))
            provenance = [json.loads(line) for line in (root/'a/provenance.jsonl').read_text().splitlines()]
            self.assertEqual(provenance[0]['source_file'], 'source.csv')
            self.assertEqual(provenance[0]['row_index'], 0)
            self.assertEqual(audit(root/'a/final_fraud_detection_dataset.csv')['total_samples'], 2)
            with self.assertRaisesRegex(ValueError, 'empty'):
                build(source, root/'a')

    def test_conflicting_duplicate_rejects_entire_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = self.fixture(root, [('same', '0', 'legitimate'), ('same', '1', 'phishing')])
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                build(source, root/'out')
            self.assertEqual(list((root/'out').iterdir()), [])

    def test_bad_label_and_category(self):
        for row in [('x', '2', 'phishing'), ('x', '0', 'phishing'), ('x', '1', 'unknown')]:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with self.assertRaises(ValueError):
                    build(self.fixture(root, [row]), root/'out')

    def test_lfs_pointer_and_missing_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root/'pointer.csv'
            source.write_text('version https://git-lfs.github.com/spec/v1\n')
            with self.assertRaisesRegex(ValueError, 'LFS'):
                audit(source)
            source.write_text('text\nx\n')
            with self.assertRaisesRegex(ValueError, 'Missing'):
                audit(source)

if __name__ == '__main__':
    unittest.main()
