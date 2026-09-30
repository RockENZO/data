# Fraud detection corpus

A research corpus combining email, SMS, job advertisements, popups and real/synthetic dialogues. The validated final artifact contains **194,913 rows: 93,196 fraud and 101,717 legitimate**, with nine categories (eight fraud categories plus legitimate). These are corpus counts, not model accuracy or independently verified annotation quality.

## Files and schema

| File | Purpose |
| --- | --- |
| `final_fraud_detection_dataset.csv` | Published training content: `text`, `binary_label`, `detailed_category`, `data_type` |
| `corrected_fraud_detection_dataset.csv` | Historical corrected corpus with source metadata; 194,914 rows including one empty text |
| `build_dataset.py` | Deterministic validated finalization and audit using the Python standard library |
| `reports/published_data_audit.json` | Counts and SHA-256 computed from the actual published CSV |
| `reports/verified_build.json` | Input/output hashes, cleaning counts and source counts from a real rebuild |
| `corrected_fraud_detection_processor.py` | Legacy raw-source ingestion, configurable paths, post-deduplication statistics |

CSV files use Git LFS. Requires Python 3.10+ and Git LFS. The final artifact has no source columns; rebuild below to obtain a matching provenance sidecar.

```bash
git lfs install
git lfs pull --include='corrected_fraud_detection_dataset.csv,final_fraud_detection_dataset.csv'
python build_dataset.py --output-dir artifacts/verified
python tests/verify_published.py
python -m unittest discover -s tests -v
```

Output: `final_fraud_detection_dataset.csv`, `provenance.jsonl`, `manifest.json`. Every accepted text has a SHA-256 sample ID and zero-based row index in the sidecar, retained dataset/source path and original label fields. The manifest hashes both output files. Existing output directories containing files are refused. The input hash is checked against the reviewed manifest by `verify_published.py`; CI verifies actual LFS contents as well as synthetic failure fixtures.

The builder removes empty texts and identical duplicate records, fails on contradictory duplicate labels/types, unknown categories, malformed CSV and missing provenance. Rebuild row values match the published final CSV; The rebuilt CSV is byte-identical to the published artifact and has the same SHA-256. Source paths are normalized to repository-relative paths.

```bash
python build_dataset.py --input final_fraud_detection_dataset.csv --audit-only
# Optional raw-source ingestion (all source LFS files and pandas/pyarrow required):
pip install -r requirements.txt
git lfs pull
python corrected_fraud_detection_processor.py --data-dir . --output artifacts/corrected.csv
python build_dataset.py --input artifacts/corrected.csv --output-dir artifacts/new-final
```

Raw ingestion is a separate recipe: upstream source files, processors and dependencies can change its result. The checked-in corrected CSV is the reviewed input for the reproducible finalization above. The historical corrected metadata recorded counts BEFORE deduplication (238,233), so it must not be used as final corpus statistics. The old README mixed pre/post-deduplication counts; the reviewed reports supersede those claims.

## Categories

| Category | Rows |
| --- | ---: |
| legitimate | 101,717 |
| phishing | 71,857 |
| popup_scam | 11,333 |
| sms_spam | 6,988 |
| reward_scam | 606 |
| tech_support_scam | 605 |
| refund_scam | 604 |
| ssn_scam | 604 |
| job_scam | 599 |

## Evaluation and limitations

- Keep provenance out of model features; retain it for audits and split design. The corrected input already dropped duplicate records, so alternate source attribution cannot be reconstructed from this input.
- An identical-text hash prevents exact leakage, but related templates and dialogue fragments may still leak. Group by original conversation/template/source and document held-out domains before reporting model performance.
- Existing source train/test exports were combined in the historical processor. The final CSV is **not** an untouched official benchmark test set. Do not reuse an upstream test split after training on this combined corpus.
- Labels inherit upstream definitions and heuristic mappings. Spam is treated as fraud in parts of this corpus; that definition is broader than financial fraud. Inspect source mappings and perform human review before deployment.
- Synthetic dialogues are not evidence of real-world scam detection performance. Report results by source/category with macro F1, per-class support, confusion matrix and false-positive rate on legitimate samples.
- Messages may contain personal data. Avoid reproducing sample content in public demos without reviewing it.

## Source attribution and rights

Source documents are retained in `difraud/README.md`, `spam dataset/README.md`, `scam dialogue/README.md`, `PopupDB-Data-main/README.md` and `Synthetic-Data-for-Scam-Detection-Leveraging-LLMs-to-Train-Deep-Learning-Models-main/README.md`.

| Source family | Evidence in repository | Status |
| --- | --- | --- |
| DIFrauD | Dataset card declares MIT | Preserve upstream attribution; check individual bundled domains |
| Spam parquet | Dataset card declares Apache-2.0 | Preserve notices and verify dataset identity |
| Synthetic scam dialogues | Upstream LICENSE and README | Read license before redistribution |
| PopupDB | Upstream LICENSE and README | Read license and underlying content conditions |
| Aggregated phishing/SMS/other dialogues | Mixed files and incomplete per-file licensing | Per-source rights review outstanding |

A repository/code license does not grant a blanket license to all messages. This corpus is a research artifact; unrestricted redistribution or commercial rights for every source have not been established. The builder preserves traceability so these reviews can be completed rather than obscured.
