import csv
import json
from pathlib import Path
import tempfile
import unittest
from build_dataset import build, audit, relative_source

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

    def test_audit_rejects_conflicting_labels_for_same_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.fixture(root,[('same','0','legitimate'),('same','1','phishing')])
            with self.assertRaisesRegex(ValueError,'Conflicting'):
                audit(source)
            source=self.fixture(root,[('same','1','phishing'),('same','1','phishing')])
            self.assertEqual(audit(source)['exact_duplicates'],1)

    def test_audit_empty_texts_do_not_conflict(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=self.fixture(root,[('valid','0','legitimate'),('', '0','legitimate'),('', '1','phishing')])
            report=audit(source)
            self.assertEqual(report['empty_texts'],2)
            self.assertEqual(report['exact_duplicates'],1)
            self.assertEqual(build(source,root/'out')['total_samples'],1)

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

    def test_ambiguous_csv_headers_are_rejected_atomically(self):
        for headers in [
            'text,text,binary_label,detailed_category,data_type,dataset,source_file',
            'text,binary_label,detailed_category,data_type,dataset,source_file,',
            'text,binary_label,detailed_category,data_type,dataset,source_file,metadata,metadata',
        ]:
            with self.subTest(headers=headers), tempfile.TemporaryDirectory() as temp:
                root=Path(temp);source=root/'input.csv'
                # A header alone must be rejected, rather than interpreted as an
                # empty corpus or silently overwrite one of the named columns.
                source.write_text(headers+'\n')
                with self.assertRaisesRegex(ValueError,'header'):
                    build(source,root/'out')
                self.assertEqual(list((root/'out').iterdir()),[])

    def test_normalized_provenance_cannot_escape_the_repository(self):
        for value in ['/Users/old/data/../secret.csv',
                      '/Users/old/data/source/../../secret.csv',
                      'C:\\old\\data\\..\\secret.csv',
                      '/Users/old/data/', '/Users/old/data/.',
                      '/Users/old/data/   ', '.']:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError,'relative'):
                    relative_source(value)
        self.assertEqual(relative_source('/Users/old/data/source/messages.csv'),
                         'source/messages.csv')

class CsvSyntaxTests(unittest.TestCase):
    def test_malformed_quotes_fail_build_and_audit_without_publication(self):
        header = 'text,binary_label,detailed_category,data_type,dataset,source_file\n'
        for record in ['message,0,legitimate,email,fixture,"source.csv',
                       'message,0,legitimate,email,fixture,"source.csv"junk\n']:
            with self.subTest(record=record), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                source = root / 'input.csv'
                source.write_text(header + record, encoding='utf-8')
                for operation in [lambda: audit(source), lambda: build(source, root / 'out')]:
                    with self.assertRaisesRegex(ValueError, 'Malformed CSV'):
                        operation()
                self.assertEqual(list((root / 'out').iterdir()), [])

    def test_valid_escaped_quotes_and_multiline_fields_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = BuildTests().fixture(root, [('He said "hello"\nnext line', '0', 'legitimate')])
            self.assertEqual(build(source, root / 'out')['total_samples'], 1)
            self.assertEqual(audit(root / 'out/final_fraud_detection_dataset.csv')['total_samples'], 1)

if __name__ == '__main__':
    unittest.main()
