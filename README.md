# Comprehensive Fraud Detection Dataset

## Overview

This repository contains a unified fraud detection dataset created by combining multiple high-quality datasets from various domains including email phishing, SMS scams, job fraud, dialogue scams, and malicious popups. The dataset is designed for training machine learning models to detect fraudulent and harmful scam content across different communication channels.

## Dataset Statistics

- **Total Samples**: 194,914 (after deduplication)
- **Fraudulent Samples**: 121,292 (51%)
- **Legitimate Samples**: 116,941 (49%)
- **Source Datasets**: 23 different datasets
- **Average Text Length**: 700 characters

### Data Type Distribution

| Data Type | Sample Count | Description |
|-----------|--------------|-------------|
| Email Classification | 164,625 | Phishing emails, spam emails, legitimate emails |
| Text Classification | 47,041 | General text content (job postings, news, etc.) |
| Popup Classification | 11,375 | Malicious popup advertisements and warnings |
| Dialogue Classification | 9,620 | Conversation data between scammers and victims |
| SMS Classification | 5,572 | Text messages including spam and legitimate SMS |

## File Structure

```
combined_fraud_detection_dataset.csv          # Main dataset file
combined_fraud_detection_dataset_metadata.json # Dataset statistics and metadata
combined_fraud_detection_dataset_sample.csv   # Sample of the data for inspection
fraud_detection_data_processor.py             # Script used to create the dataset
README.md                                      # This documentation file
```

## Dataset Schema

The main dataset file (`combined_fraud_detection_dataset.csv`) contains the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `text` | string | The main text content to be classified |
| `label` | integer | Binary label (0 = legitimate, 1 = fraudulent/scam) |
| `dataset` | string | Source dataset identifier |
| `source_file` | string | Original file path of the data |
| `data_type` | string | Type of classification task |
| `dialogue_type` | string | (Optional) Type of dialogue for conversation data |
| `domain` | string | (Optional) Domain information for popup data |
| `country` | string | (Optional) Country information for popup data |

## Source Datasets

### 1. DIFrauD Benchmark Datasets
- **Job Scams**: Employment fraud detection (14,295 samples)
- **Phishing**: Email phishing detection (15,272 samples)
- **SMS**: SMS spam detection (6,574 samples)

### 2. Spam Datasets
- **Main Spam CSV**: SMS spam classification (5,572 samples)
- **Parquet Format**: Additional spam data (10,900 samples)

### 3. Phishing Email Datasets
- **Multiple Sources**: CEAS_08, Enron, Ling, Nazario, Nigerian_Fraud, SpamAssasin, and others
- **Total**: 164,625 email samples

### 4. Scam Dialogue Datasets
- **Real Conversations**: Actual scammer-victim dialogues
- **Synthetic Data**: LLM-generated scam conversations
- **Total**: 9,620 dialogue samples

### 5. PopupDB
- **Malicious Popups**: Database of scam popup advertisements
- **Total**: 11,375 popup samples

## Data Quality Features

### Text Preprocessing
- Whitespace normalization
- Removal of null bytes and problematic characters
- Text length limitation (max 10,000 characters)
- Unicode normalization

### Label Standardization
- All labels converted to binary format (0/1)
- Consistent mapping across different source label formats
- Handles various label types: spam/ham, fraud/legitimate, etc.

### Deduplication
- Removed 43,319 duplicate entries based on text content
- Ensures unique samples in the final dataset

## Usage Examples

### Loading the Dataset

```python
import pandas as pd

# Load the main dataset
df = pd.read_csv('combined_fraud_detection_dataset.csv')

# Basic information
print(f"Dataset shape: {df.shape}")
print(f"Fraud ratio: {df['label'].mean():.3f}")
print(f"Data types: {df['data_type'].value_counts()}")
```

### Train/Test Split by Dataset Type

```python
from sklearn.model_selection import train_test_split

# Split by maintaining dataset distribution
X = df['text']
y = df['label']
groups = df['dataset']

# Stratified split maintaining label balance
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
```

### Basic Text Classification

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Feature extraction
vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Model training
model = LogisticRegression()
model.fit(X_train_vec, y_train)

# Evaluation
y_pred = model.predict(X_test_vec)
print(classification_report(y_test, y_pred))
```

### Domain-Specific Analysis

```python
# Analyze performance by data type
for data_type in df['data_type'].unique():
    subset = df[df['data_type'] == data_type]
    fraud_rate = subset['label'].mean()
    print(f"{data_type}: {len(subset)} samples, {fraud_rate:.1%} fraud rate")
```

## Recommended Use Cases

### 1. Multi-Domain Fraud Detection
Train models that can generalize across different types of fraudulent content:
- Email phishing detection
- SMS spam filtering
- Job scam identification
- Conversation-based scam detection

### 2. Transfer Learning Research
Use the dataset to study how fraud detection models perform across domains:
- Cross-domain generalization
- Domain adaptation techniques
- Few-shot learning for new fraud types

### 3. Feature Engineering Research
The diverse content types allow for studying:
- Text representation methods
- Domain-specific features
- Multi-modal fraud detection

### 4. Evaluation Benchmarking
Compare fraud detection approaches across:
- Traditional ML methods (SVM, Random Forest)
- Deep learning models (LSTM, BERT)
- Ensemble methods

## Model Performance Baselines

### Recommended Evaluation Metrics
- **Precision**: Important for reducing false positives
- **Recall**: Critical for catching actual fraud
- **F1-Score**: Balanced metric for overall performance
- **AUC-ROC**: Good for ranking/probability outputs

### Cross-Domain Evaluation
When evaluating models, consider:
1. **In-domain performance**: Train and test on same data type
2. **Cross-domain performance**: Train on one type, test on another
3. **Multi-domain performance**: Train on mixed data, test on each type

## Data Ethics and Considerations

### Privacy
- All personal information has been removed or anonymized
- No real phone numbers, emails, or addresses are exposed
- Synthetic data is clearly marked

### Bias Considerations
- Dataset contains content from multiple sources and time periods
- Geographic bias may exist (primarily English-language content)
- Consider demographic representation when deploying models

### Responsible Use
- Models should be tested thoroughly before deployment
- Consider false positive impact on legitimate communications
- Regular model updates recommended as fraud tactics evolve

## Citation and Attribution

If you use this dataset in your research, please cite the original source datasets:

### DIFrauD Dataset
```
@inproceedings{boumber-etal-2024-domain,
    title = "Domain-Agnostic Adapter Architecture for Deception Detection: Extensive Evaluations with the {DIF}rau{D} Benchmark",
    author = "Boumber, Dainis A. and Qachfar, Fatima Zahra and Verma, Rakesh",
    booktitle = "Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)",
    year = "2024"
}
```

### Synthetic Scam Detection Data
Please refer to the original repository for appropriate citations.

## License

This dataset combines multiple sources with different licenses. Please refer to the original datasets for specific licensing terms. The processing script is provided under MIT license for educational and research purposes.

## Technical Support

### Common Issues

1. **Memory Errors**: The dataset is large (194k samples). Consider:
   - Loading data in chunks
   - Using sampling for initial experiments
   - Increasing available RAM

2. **Encoding Issues**: If you encounter text encoding problems:
   - Use `encoding='utf-8'` when loading CSV
   - Consider using `errors='ignore'` for problematic characters

3. **Class Imbalance**: The dataset is relatively balanced (51%/49%), but for specific subsets:
   - Use stratified sampling
   - Consider class weights in model training
   - Apply resampling techniques if needed

### Performance Optimization

- Use vectorization for text processing
- Consider using sparse matrices for large feature sets
- Implement batch processing for large-scale training

## Future Updates

This dataset will be updated periodically to include:
- New fraud detection datasets
- Improved preprocessing techniques
- Additional metadata fields
- Performance benchmarks from different models

---

**Created**: August 2025  
**Last Updated**: August 2025  
**Version**: 1.0
