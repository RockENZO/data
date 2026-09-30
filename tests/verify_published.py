"""Verify published counts, exact row equality and deterministic build manifest."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import csv
import json
from build_dataset import audit
report = audit('final_fraud_detection_dataset.csv')
expected = json.loads(Path('reports/published_data_audit.json').read_text())
assert report == expected, 'Published dataset differs from verified audit'
assert report['empty_texts'] == report['exact_duplicates'] == 0
assert json.loads(Path('artifacts/verified/manifest.json').read_text()) == json.loads(Path('reports/verified_build.json').read_text())
with open('final_fraud_detection_dataset.csv', newline='') as published, open('artifacts/verified/final_fraud_detection_dataset.csv', newline='') as rebuilt:
    assert list(csv.DictReader(published)) == list(csv.DictReader(rebuilt)), 'Rebuild differs from published rows'
print('PASS: published data, metadata, provenance manifest and rebuilt row equality')
