"""Verify the published corpus and the actual bytes of the rebuilt artifacts."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_dataset import audit, sha256


def verify_published(root):
    published = root / 'final_fraud_detection_dataset.csv'
    reports = root / 'reports'
    rebuilt = root / 'artifacts' / 'verified'
    report = audit(published)
    expected = json.loads((reports / 'published_data_audit.json').read_text())
    if report != expected:
        raise ValueError('Published dataset differs from verified audit')
    if report['empty_texts'] or report['exact_duplicates']:
        raise ValueError('Published dataset contains empty or duplicate records')

    manifest = json.loads((reports / 'verified_build.json').read_text())
    if json.loads((rebuilt / 'manifest.json').read_text()) != manifest:
        raise ValueError('Rebuild manifest differs from verified build')
    if report['input_sha256'] != manifest['output_sha256']:
        raise ValueError('Published CSV differs from verified build')
    if sha256(rebuilt / published.name) != manifest['output_sha256']:
        raise ValueError('Rebuilt CSV differs from verified build')
    if sha256(rebuilt / 'provenance.jsonl') != manifest['provenance_sha256']:
        raise ValueError('Rebuilt provenance differs from verified build')


if __name__ == '__main__':
    try:
        verify_published(Path.cwd())
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f'Validation failed: {error}')
    print('PASS: published data, rebuild manifest and rebuilt artifact hashes')
