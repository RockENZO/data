import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_dataset as dataset


class PublicationTests(unittest.TestCase):
    def test_late_existing_artifact_is_preserved_without_unlinking_published_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'input.csv'; out = root/'out'
            with source.open('w',newline='') as stream:
                writer = csv.writer(stream); writer.writerow([*dataset.COLUMNS,'dataset','source_file']);writer.writerow(['Hello','0','legitimate','email','fixture','messages.csv'])
            original_hash = dataset.sha256
            def arriving_file(path):
                if Path(path).name == 'final_fraud_detection_dataset.csv':
                    (out/'provenance.jsonl').write_bytes(b'other process artifact')
                return original_hash(path)
            with patch.object(dataset, 'sha256', arriving_file):
                with self.assertRaises(FileExistsError):dataset.build(source,out)
            self.assertEqual((out/'provenance.jsonl').read_bytes(),b'other process artifact')
            self.assertEqual({p.name for p in out.iterdir()}, {'provenance.jsonl', 'final_fraud_detection_dataset.csv'})
            self.assertFalse((out/'manifest.json').exists())

    def test_failed_publication_never_checks_then_unlinks_a_published_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'input.csv'; out = root/'out'
            source.write_text('text,binary_label,detailed_category,data_type,dataset,source_file\nHello,0,legitimate,email,fixture,messages.csv\n')
            original_link = dataset.os.link
            def fail_second_link(source_path, target_path):
                if Path(target_path).name == 'provenance.jsonl':
                    replacement = root/'replacement'; replacement.write_bytes(b'other writer replacement')
                    replacement.replace(out/'final_fraud_detection_dataset.csv')
                    raise OSError('simulated publication interruption')
                return original_link(source_path, target_path)
            with patch.object(dataset.os, 'link', fail_second_link), patch.object(dataset.os.path, 'samefile') as ownership_check:
                with self.assertRaises(OSError):dataset.build(source,out)
            ownership_check.assert_not_called()
            self.assertEqual((out/'final_fraud_detection_dataset.csv').read_bytes(), b'other writer replacement')
            self.assertFalse((out/'manifest.json').exists())

    def test_regular_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); out = root/'out';out.mkdir();marker=out/'manifest.json';marker.write_bytes(b'keep')
            with self.assertRaises(ValueError):dataset.build(root/'missing.csv',out)
            self.assertEqual(marker.read_bytes(),b'keep')
