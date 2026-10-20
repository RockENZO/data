import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_dataset as dataset


class PublicationTests(unittest.TestCase):
    def test_late_existing_artifact_is_preserved_and_own_links_rolled_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'input.csv'; out = root/'out'
            with source.open('w',newline='') as stream:
                writer = csv.writer(stream); writer.writerow([*dataset.COLUMNS,'dataset','source_file']);writer.writerow(['Hello','0','legitimate','email','fixture','messages.csv'])
            original_hash = dataset.sha256
            def arriving_file(path):
                if Path(path) == source:
                    (out/'provenance.jsonl').write_bytes(b'other process artifact')
                return original_hash(path)
            with patch.object(dataset, 'sha256', arriving_file):
                with self.assertRaises(FileExistsError):dataset.build(source,out)
            self.assertEqual((out/'provenance.jsonl').read_bytes(),b'other process artifact')
            self.assertEqual([p.name for p in out.iterdir()],['provenance.jsonl'])

    def test_regular_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); out = root/'out';out.mkdir();marker=out/'manifest.json';marker.write_bytes(b'keep')
            with self.assertRaises(ValueError):dataset.build(root/'missing.csv',out)
            self.assertEqual(marker.read_bytes(),b'keep')
