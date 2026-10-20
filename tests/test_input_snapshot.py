import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from build_dataset import build, audit


class SnapshotTests(unittest.TestCase):
    def test_build_and_audit_identify_parsed_input_after_source_changes(self):
        for operation in ['build', 'audit']:
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); source = root/'input.csv'
                original = b'\xef\xbb\xbftext,binary_label,detailed_category,data_type,dataset,source_file\r\nHello,0,legitimate,email,fixture,messages.csv\r\n'
                source.write_bytes(original)
                real_read = Path.read_bytes
                def mutate_after_read(path):
                    value = real_read(path)
                    if path == source: path.write_bytes(b'changed after reading')
                    return value
                with patch.object(Path, 'read_bytes', mutate_after_read):
                    report = build(source, root/'out') if operation == 'build' else audit(source)
                self.assertEqual(report['input_sha256'], hashlib.sha256(original).hexdigest())
                self.assertEqual(report['total_samples'], 1)
                if operation == 'build':
                    self.assertIn('Hello', (root/'out/final_fraud_detection_dataset.csv').read_text())
