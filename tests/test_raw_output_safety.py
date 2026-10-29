"""Exercise real pandas CSV/metadata writes without ingesting private source data."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec('pandas'), 'optional raw-ingestion pandas dependency')
class RawOutputTests(unittest.TestCase):
    def run_recipe(self, output, before_save=None):
        import corrected_fraud_detection_processor as raw
        processor = raw.CorrectedFraudDataProcessor(str(output.parent))
        processor.combined_data = [dict(text='synthetic fixture', binary_label=0,
            detailed_category='legitimate', confidence='high', dataset='fixture',
            data_type='email', source_file='fixture.csv')]
        if before_save:
            real_save = processor.save_corrected_dataset
            def save(path):
                before_save()
                return real_save(path)
            processor.save_corrected_dataset = save
        with patch('sys.argv', ['processor', '--output', str(output)]), \
             patch.object(raw, 'CorrectedFraudDataProcessor', return_value=processor), \
             patch.object(processor, 'process_all_datasets'):
            raw.main()

    def test_names_without_lowercase_csv_keep_dataset_and_sidecars_distinct(self):
        for name in ['corrected', 'corrected.CSV', 'corrected.csv', 'corrected.csv.backup']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                output = Path(temp)/'parent.csv.folder'/name
                self.run_recipe(output)
                with output.open(newline='') as f:
                    self.assertEqual(list(csv.DictReader(f))[0]['text'], 'synthetic fixture')
                metadata = output.with_name(output.stem + '_metadata.json')
                samples = output.with_name(output.stem + '_category_samples.csv')
                self.assertEqual(json.loads(metadata.read_text())['statistics_stage'], 'post_deduplication')
                self.assertTrue(samples.is_file())

    def test_existing_sidecars_and_dangling_symlinks_refuse_entire_recipe(self):
        for suffix in ['_metadata.json', '_category_samples.csv']:
            for dangling in [False, True]:
                with self.subTest(suffix=suffix, dangling=dangling), tempfile.TemporaryDirectory() as temp:
                    output = Path(temp)/'corrected.csv'
                    other = output.with_name(output.stem + suffix)
                    if dangling:
                        other.symlink_to(Path(temp)/'absent-target')
                    else:
                        other.write_bytes(b'existing user content')
                    with self.assertRaises(SystemExit):
                        self.run_recipe(output)
                    self.assertFalse(output.exists())
                    if dangling:
                        self.assertTrue(other.is_symlink())
                        self.assertFalse(other.resolve().exists())
                    else:
                        self.assertEqual(other.read_bytes(), b'existing user content')

    def test_primary_output_appearing_after_preflight_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'corrected.csv'
            with self.assertRaises(FileExistsError):
                self.run_recipe(output, lambda: output.write_bytes(b'concurrent writer'))
            self.assertEqual(output.read_bytes(), b'concurrent writer')

    def test_metadata_appearing_after_preflight_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'corrected.csv'
            metadata=Path(temp)/'corrected_metadata.json'
            with self.assertRaises(FileExistsError):
                self.run_recipe(output, lambda: metadata.write_bytes(b'concurrent metadata'))
            self.assertEqual(metadata.read_bytes(), b'concurrent metadata')
