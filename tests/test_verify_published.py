import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from build_dataset import audit, build


class PublishedVerificationTests(unittest.TestCase):
    def test_detects_changed_rebuilt_bytes_even_under_optimization(self):
        script = Path(__file__).with_name('verify_published.py').resolve()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'input.csv'
            source.write_text(
                'text,binary_label,detailed_category,data_type,dataset,source_file\n'
                'Example,0,legitimate,email,sample,example.csv\n',
                encoding='utf-8',
            )
            rebuilt = root / 'artifacts' / 'verified'
            manifest = build(source, rebuilt)
            csv_name = 'final_fraud_detection_dataset.csv'
            published = root / csv_name
            published.write_bytes((rebuilt / csv_name).read_bytes())
            reports = root / 'reports'
            reports.mkdir()
            (reports / 'published_data_audit.json').write_text(json.dumps(audit(published)))
            (reports / 'verified_build.json').write_text(json.dumps(manifest))

            def run():
                return subprocess.run(
                    [sys.executable, '-O', str(script)], cwd=root, capture_output=True, text=True,
                )

            clean = run()
            self.assertEqual(clean.returncode, 0, clean.stderr)
            for name, message in [(csv_name, 'Rebuilt CSV'), ('provenance.jsonl', 'Rebuilt provenance')]:
                with self.subTest(name=name):
                    path = rebuilt / name
                    original = path.read_bytes()
                    # Add a UTF-8 BOM. Parsed CSV rows remain the same.
                    path.write_bytes(b'\xef\xbb\xbf' + original)
                    failed = run()
                    path.write_bytes(original)
                    self.assertNotEqual(failed.returncode, 0)
                    self.assertIn(message, failed.stderr)
