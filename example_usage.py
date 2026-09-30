"""Print verified corpus statistics without fitting a model on mixed source splits."""
import argparse
import json
from pathlib import Path
from build_dataset import audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('final_fraud_detection_dataset.csv'))
    args = parser.parse_args()
    print(json.dumps(audit(args.input), indent=2, sort_keys=True))
