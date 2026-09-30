"""Auditable, deterministic finalization of the corrected source CSV (stdlib only)."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import tempfile

COLUMNS = ('text', 'binary_label', 'detailed_category', 'data_type')
CATEGORIES = ('legitimate', 'phishing', 'popup_scam', 'sms_spam', 'reward_scam',
              'tech_support_scam', 'refund_scam', 'ssn_scam', 'job_scam')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_rows(path, provenance=False):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        if stream.readline().startswith('version https://git-lfs.github.com/spec'):
            raise ValueError('Git LFS pointer found; run git lfs pull before building')
        stream.seek(0)
        reader = csv.DictReader(stream)
        required = set(COLUMNS) | ({'dataset', 'source_file'} if provenance else set())
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Missing columns: ' + ', '.join(sorted(required - set(reader.fieldnames or []))))
        for number, row in enumerate(reader, 2):
            if None in row or any(row.get(key) is None for key in required):
                raise ValueError(f'Malformed CSV record {number}')
            yield number, row


def validate_label(row, number):
    if row['binary_label'] not in ('0', '1'):
        raise ValueError(f'Invalid binary label at record {number}')
    if row['detailed_category'] not in CATEGORIES:
        raise ValueError(f'Unknown category at record {number}')
    if (row['binary_label'] == '0') != (row['detailed_category'] == 'legitimate'):
        raise ValueError(f'Binary/category contradiction at record {number}')
    if not row['data_type'].strip():
        raise ValueError(f'Empty data_type at record {number}')


def relative_source(value):
    # Historical corrected CSV stored machine-specific absolute paths.
    normalized = value.replace('\\', '/')
    marker = '/data/'
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    path = Path(normalized)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Source path cannot be made repository relative')
    return path.as_posix()


def build(input_path, output_dir):
    input_path, output_dir = Path(input_path), Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('Output directory must be empty; existing artifacts are never overwritten')
    output_dir.mkdir(parents=True, exist_ok=True)
    categories, types, sources, labels = (Counter() for _ in range(4))
    seen = {}
    empty = duplicates = input_rows = 0
    # Validate and write in a temporary directory; publish only after the full input passes.
    with tempfile.TemporaryDirectory(dir=output_dir) as staging:
        staging = Path(staging)
        with (staging / 'final_fraud_detection_dataset.csv').open('w', encoding='utf-8', newline='') as final, (staging / 'provenance.jsonl').open('w', encoding='utf-8') as provenance:
            writer = csv.DictWriter(final, fieldnames=COLUMNS, lineterminator='\n')
            writer.writeheader()
            for number, row in read_rows(input_path, provenance=True):
                input_rows += 1
                validate_label(row, number)
                if not row['text'].strip():
                    empty += 1
                    continue
                sample_id = hashlib.sha256(row['text'].encode('utf-8')).hexdigest()
                identity = tuple(row[key] for key in COLUMNS[1:])
                if sample_id in seen:
                    if seen[sample_id] != identity:
                        raise ValueError(f'Conflicting labels/type for identical text at record {number}')
                    duplicates += 1
                    continue
                seen[sample_id] = identity
                if not row['dataset'].strip() or not row['source_file'].strip():
                    raise ValueError(f'Missing provenance at record {number}')
                writer.writerow({key: row[key] for key in COLUMNS})
                provenance.write(json.dumps({'row_index': len(seen)-1, 'sample_id': sample_id,
                    'dataset': row['dataset'], 'source_file': relative_source(row['source_file']),
                    'source_record_in_corrected_csv': number-1,
                    'original_label': row.get('original_label'), 'original_type': row.get('original_type')}, ensure_ascii=False, sort_keys=True) + '\n')
                categories[row['detailed_category']] += 1
                types[row['data_type']] += 1
                sources[row['dataset']] += 1
                labels[row['binary_label']] += 1
        if not seen:
            raise ValueError('Input has no valid non-empty records')
        report = {'schema_version': 1, 'input_sha256': sha256(input_path),
            'input_rows': input_rows, 'total_samples': len(seen), 'empty_rows_removed': empty,
            'exact_duplicates_removed': duplicates, 'fraud_samples': labels['1'],
            'legitimate_samples': labels['0'], 'columns': list(COLUMNS),
            'detailed_categories': dict(sorted(categories.items())), 'data_types': dict(sorted(types.items())),
            'source_datasets': dict(sorted(sources.items())),
            'output_sha256': sha256(staging / 'final_fraud_detection_dataset.csv'),
            'provenance_sha256': sha256(staging / 'provenance.jsonl'),
            'limitations': ['Corrected input already discarded duplicate source records; alternate provenance cannot be recovered.',
                'Labels are inherited from upstream processors, not independently adjudicated.',
                'Text hashes prevent exact duplicate leakage only; source/template grouping is needed for evaluation.']}
        (staging / 'manifest.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
        for artifact in staging.iterdir():
            artifact.replace(output_dir / artifact.name)
    return report


def audit(input_path):
    labels, categories, types = Counter(), Counter(), Counter()
    seen = set()
    empty = duplicates = total = 0
    for number, row in read_rows(input_path):
        validate_label(row, number)
        total += 1
        empty += not bool(row['text'].strip())
        digest = hashlib.sha256(row['text'].encode('utf-8')).hexdigest()
        duplicates += digest in seen
        seen.add(digest)
        labels[row['binary_label']] += 1
        categories[row['detailed_category']] += 1
        types[row['data_type']] += 1
    return {'input_sha256': sha256(input_path), 'total_samples': total,
            'fraud_samples': labels['1'], 'legitimate_samples': labels['0'],
            'empty_texts': empty, 'exact_duplicates': duplicates,
            'detailed_categories': dict(sorted(categories.items())), 'data_types': dict(sorted(types.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('corrected_fraud_detection_dataset.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('artifacts/final'))
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    try:
        report = audit(args.input) if args.audit_only else build(args.input, args.output_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Validation failed: {error}\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
