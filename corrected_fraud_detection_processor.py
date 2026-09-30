#!/usr/bin/env python3
"""
Corrected Enhanced Fraud Detection Dataset Processor

This script fixes the labeling issues where legitimate activities were incorrectly
categorized as scam subtypes. It properly distinguishes between scam types and 
legitimate communication types.

Key corrections:
- Properly interprets label=0 as legitimate and label=1 as fraudulent
- Correctly categorizes scam types only for actual scams (label=1)
- Fixes misclassification of appointment confirmations, delivery notifications, etc.
- Maintains proper multi-class labeling for actual fraud categories

Output: A correctly labeled dataset with accurate fraud subcategories.
"""

import pandas as pd
import json
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import warnings
from collections import defaultdict, Counter

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CorrectedFraudDataProcessor:
    """Corrected processor for creating properly labeled multi-class fraud detection datasets."""
    
    def __init__(self, data_directory: str):
        """
        Initialize the corrected processor.
        
        Args:
            data_directory: Path to the directory containing all datasets
        """
        self.data_dir = Path(data_directory)
        self.combined_data = []
        
        # Define ACTUAL scam/fraud taxonomy (only for label=1 cases)
        self.fraud_taxonomy = {
            # Government/Authority Impersonation Scams
            'ssn_scam': ['ssn', 'social_security', 'ssa'],
            'irs_scam': ['irs', 'tax_scam', 'tax_fraud'],
            'government_impersonation': ['government_agency', 'federal_trade_commission'],
            
            # Financial/Payment Scams
            'refund_scam': ['refund', 'overpayment', 'fake_refund'],
            'reward_scam': ['reward', 'prize', 'lottery', 'sweepstakes', 'gift_card'],
            'credit_card_scam': ['credit_card_fraud', 'unauthorized_charge'],
            'investment_scam': ['investment_fraud', 'ponzi', 'pyramid'],
            
            # Tech Support Scams
            'tech_support_scam': ['support', 'technical_support', 'microsoft_scam', 'computer_virus'],
            'virus_scam': ['virus_warning', 'malware_alert', 'computer_infection'],
            
            # Service/Business Scams
            'telemarketing_scam': ['telemarketing', 'cold_call_scam', 'unsolicited_sales'],
            'job_scam': ['employment_fraud', 'fake_job', 'work_from_home_scam'],
            
            # Communication Scams
            'phishing': ['phishing', 'email_scam', 'credential_theft'],
            'sms_spam': ['sms_spam', 'text_scam', 'spam_message'],
            'romance_scam': ['romance_fraud', 'dating_scam', 'catfishing'],
            
            # Other Scams
            'popup_scam': ['popup_fraud', 'fake_popup', 'browser_warning'],
            'charity_scam': ['fake_charity', 'donation_fraud'],
            'delivery_scam': ['fake_delivery', 'package_scam', 'shipping_fraud'],
            'insurance_scam': ['insurance_fraud', 'fake_insurance'],
            'wrong_number_scam': ['wrong_number', 'misdial_scam']
        }
        
        # Legitimate communication types (these are NOT scams when label=0)
        self.legitimate_types = {
            'appointment', 'delivery', 'insurance', 'telemarketing', 'wrong', 
            'appointment_confirmation', 'delivery_notification', 'insurance_communication',
            'legitimate_telemarketing', 'wrong_number', 'customer_service', 'survey'
        }
        
        # Reverse mapping for quick lookup
        self.category_lookup = {}
        for category, keywords in self.fraud_taxonomy.items():
            for keyword in keywords:
                self.category_lookup[keyword.lower()] = category
        
        # Statistics tracking
        self.processing_stats = defaultdict(int)
        self.label_distribution = defaultdict(int)
        self.correction_stats = defaultdict(int)
        
    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning with better preprocessing."""
        if pd.isna(text) or text is None:
            return ""
        
        # Convert to string
        text = str(text)
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove problematic characters but preserve structure
        text = text.replace('\x00', '').replace('\r', ' ')
        # Keep newlines for dialogue structure but normalize multiple newlines
        text = re.sub(r'\n\s*\n', ' | ', text)  # Convert paragraph breaks to separators
        text = text.replace('\n', ' ')
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)  # Normalize ellipsis
        text = re.sub(r'[!]{2,}', '!', text)    # Normalize exclamation
        text = re.sub(r'[?]{2,}', '?', text)    # Normalize questions
        
        # Limit text length
        if len(text) > 15000:
            text = text[:15000] + "..."
            
        return text
    
    def categorize_fraud_type(self, label_info: Dict[str, Any], dataset_type: str) -> Tuple[str, int, str]:
        """
        CORRECTED fraud categorization that properly handles legitimate vs fraudulent labels.
        
        Args:
            label_info: Dictionary containing label information
            dataset_type: Type of dataset for context
            
        Returns:
            Tuple of (detailed_category, binary_label, confidence)
        """
        # Extract label fields
        original_label = label_info.get('label', 0)
        scam_type = label_info.get('type', '').lower().strip()
        source_file = label_info.get('source_file', '').lower()
        dataset = label_info.get('dataset', '').lower()
        
        # Determine binary label first
        binary_label = 0  # Default to legitimate
        confidence = "high"
        
        # Check explicit binary labels
        if isinstance(original_label, (int, str)):
            label_str = str(original_label).lower().strip()
            if label_str in ['1', 'true', 'spam', 'scam', 'fraud', 'phishing', 'deceptive']:
                binary_label = 1
            elif label_str in ['0', 'false', 'ham', 'legitimate', 'not_spam', 'truthful']:
                binary_label = 0
        
        # Special handling for PopupDB (all entries are malicious)
        if 'popupdb' in dataset_type.lower():
            binary_label = 1
            confidence = "high"
        
        # Now determine detailed category based on binary label
        if binary_label == 0:
            # This is legitimate communication
            detailed_category = "legitimate"
            
            # Track what types of legitimate communication we're seeing
            if scam_type in self.legitimate_types:
                self.correction_stats[f'legitimate_{scam_type}'] += 1
            else:
                self.correction_stats['legitimate_other'] += 1
                
        else:
            # This is actual fraud - categorize the scam type
            detailed_category = "unknown_fraud"
            
            # First check if we have explicit scam type mapping
            if scam_type:
                # Check direct mapping
                category = self.category_lookup.get(scam_type)
                if category:
                    detailed_category = category
                else:
                    # Try to infer from type text
                    detailed_category = self._infer_fraud_category_from_text(scam_type)
            
            # If still unknown, check dataset source for hints
            if detailed_category == "unknown_fraud":
                if 'phishing' in dataset or 'phishing' in source_file:
                    detailed_category = "phishing"
                elif 'sms' in dataset or 'sms' in source_file:
                    detailed_category = "sms_spam" 
                elif 'job' in dataset or 'job' in source_file:
                    detailed_category = "job_scam"
                elif 'popup' in dataset or 'popup' in source_file:
                    detailed_category = "popup_scam"
                elif 'spam' in dataset:
                    detailed_category = "sms_spam"
        
        return detailed_category, binary_label, confidence
    
    def _infer_fraud_category_from_text(self, text: str) -> str:
        """Infer fraud category from text content (only for confirmed frauds)."""
        text = text.lower()
        
        # Social Security / Government scams
        if any(term in text for term in ['ssn', 'social security', 'social_security', 'ssa']):
            return "ssn_scam"
        
        # Tech support scams
        if any(term in text for term in ['support', 'technical support', 'tech support', 'microsoft', 'windows', 'computer', 'virus', 'malware']):
            return "tech_support_scam"
        
        # Financial scams
        if any(term in text for term in ['refund', 'reimburs', 'money back']):
            return "refund_scam"
        
        # Reward/Prize scams
        if any(term in text for term in ['reward', 'prize', 'winner', 'congratulation', 'gift card', 'lottery']):
            return "reward_scam"
        
        # Service-related fraud
        if any(term in text for term in ['telemarketing', 'sales']):
            return "telemarketing_scam"
        
        return "unknown_fraud"
    
    def process_difraud_datasets(self):
        """Process DIFrauD benchmark datasets with corrected categorization."""
        logger.info("Processing DIFrauD datasets...")
        
        difraud_dir = self.data_dir / "difraud"
        if not difraud_dir.exists():
            logger.warning("DIFrauD directory not found, skipping...")
            return
        
        for domain_dir in difraud_dir.iterdir():
            if domain_dir.is_dir() and domain_dir.name not in ['__pycache__', '.git']:
                domain_name = domain_dir.name.replace(' ', '_')
                logger.info(f"  Processing DIFrauD {domain_name}...")
                
                for split_file in domain_dir.glob("*.jsonl"):
                    try:
                        with open(split_file, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                try:
                                    data = json.loads(line.strip())
                                    
                                    label_info = {
                                        'label': data.get('label', 0),
                                        'type': domain_name,  # Use domain as type
                                        'source_file': str(split_file),
                                        'dataset': f'difraud_{domain_name}'
                                    }
                                    
                                    detailed_category, binary_label, confidence = self.categorize_fraud_type(
                                        label_info, f'difraud_{domain_name}'
                                    )
                                    
                                    self.combined_data.append({
                                        'text': self.clean_text(data.get('text', '')),
                                        'binary_label': binary_label,
                                        'detailed_category': detailed_category,
                                        'dataset': f'difraud_{domain_name}',
                                        'source_file': str(split_file),
                                        'data_type': 'text_classification',
                                        'confidence': confidence,
                                        'original_label': data.get('label'),
                                        'original_type': domain_name
                                    })
                                    
                                    self.processing_stats[f'difraud_{domain_name}'] += 1
                                    self.label_distribution[detailed_category] += 1
                                    
                                except json.JSONDecodeError as e:
                                    logger.warning(f"JSON decode error in {split_file} line {line_num}: {e}")
                                    continue
                    except Exception as e:
                        logger.error(f"Error processing {split_file}: {e}")
                        continue
    
    def process_dialogue_datasets(self):
        """Process scam dialogue datasets with CORRECTED subcategory handling."""
        logger.info("Processing dialogue datasets with corrected labeling...")
        
        # Process main scam dialogue directory
        scam_dir = self.data_dir / "scam dialogue"
        if scam_dir.exists():
            for csv_file in scam_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    dataset_name = f'scam_dialogue_{csv_file.stem}'
                    
                    for _, row in df.iterrows():
                        if pd.notna(row.get('dialogue')):
                            label_info = {
                                'label': row.get('label', 0),
                                'type': row.get('type', ''),
                                'source_file': str(csv_file),
                                'dataset': dataset_name
                            }
                            
                            detailed_category, binary_label, confidence = self.categorize_fraud_type(
                                label_info, dataset_name
                            )
                            
                            self.combined_data.append({
                                'text': self.clean_text(row['dialogue']),
                                'binary_label': binary_label,
                                'detailed_category': detailed_category,
                                'dataset': dataset_name,
                                'source_file': str(csv_file),
                                'data_type': 'dialogue_classification',
                                'confidence': confidence,
                                'original_label': row.get('label'),
                                'original_type': row.get('type', 'unknown')
                            })
                            
                            self.processing_stats[dataset_name] += 1
                            self.label_distribution[detailed_category] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing {csv_file}: {e}")
        
        # Process synthetic dialogue datasets
        synthetic_dir = self.data_dir / "Synthetic-Data-for-Scam-Detection-Leveraging-LLMs-to-Train-Deep-Learning-Models-main" / "data"
        if synthetic_dir.exists():
            for csv_file in synthetic_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file)
                    dataset_name = f'synthetic_{csv_file.stem}'
                    
                    # Handle different column naming
                    dialogue_col = 'dialogue' if 'dialogue' in df.columns else 'conversation'
                    label_col = 'labels' if 'labels' in df.columns else 'label'
                    
                    if dialogue_col not in df.columns:
                        continue
                    
                    for _, row in df.iterrows():
                        if pd.notna(row.get(dialogue_col)):
                            label_info = {
                                'label': row.get(label_col, 0),
                                'type': row.get('type', ''),
                                'source_file': str(csv_file),
                                'dataset': dataset_name
                            }
                            
                            detailed_category, binary_label, confidence = self.categorize_fraud_type(
                                label_info, dataset_name
                            )
                            
                            self.combined_data.append({
                                'text': self.clean_text(row[dialogue_col]),
                                'binary_label': binary_label,
                                'detailed_category': detailed_category,
                                'dataset': dataset_name,
                                'source_file': str(csv_file),
                                'data_type': 'dialogue_classification',
                                'confidence': confidence,
                                'original_label': row.get(label_col),
                                'original_type': row.get('type', 'unknown')
                            })
                            
                            self.processing_stats[dataset_name] += 1
                            self.label_distribution[detailed_category] += 1
                            
                except Exception as e:
                    logger.error(f"Error processing {csv_file}: {e}")
    
    def process_spam_datasets(self):
        """Process spam datasets."""
        logger.info("Processing spam datasets...")
        
        # Process main spam.csv
        spam_csv = self.data_dir / "spam.csv"
        if spam_csv.exists():
            try:
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(spam_csv, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    logger.warning("Could not decode spam.csv, skipping...")
                    return
                
                for _, row in df.iterrows():
                    if pd.notna(row.get('v2')):
                        label_info = {
                            'label': row['v1'],
                            'type': 'sms',
                            'source_file': str(spam_csv),
                            'dataset': 'spam_main'
                        }
                        
                        detailed_category, binary_label, confidence = self.categorize_fraud_type(
                            label_info, 'spam_main'
                        )
                        
                        self.combined_data.append({
                            'text': self.clean_text(row['v2']),
                            'binary_label': binary_label,
                            'detailed_category': detailed_category,
                            'dataset': 'spam_main',
                            'source_file': str(spam_csv),
                            'data_type': 'sms_classification',
                            'confidence': confidence,
                            'original_label': row['v1'],
                            'original_type': 'sms'
                        })
                        
                        self.processing_stats['spam_main'] += 1
                        self.label_distribution[detailed_category] += 1
                        
            except Exception as e:
                logger.error(f"Error processing spam.csv: {e}")
        
        # Process spam parquet files
        spam_dir = self.data_dir / "spam dataset" / "spam"
        if spam_dir.exists():
            for parquet_file in spam_dir.glob("*.parquet"):
                try:
                    df = pd.read_parquet(parquet_file)
                    
                    for _, row in df.iterrows():
                        label_info = {
                            'label': row['label'],
                            'type': 'spam',
                            'source_file': str(parquet_file),
                            'dataset': 'spam_parquet'
                        }
                        
                        detailed_category, binary_label, confidence = self.categorize_fraud_type(
                            label_info, 'spam_parquet'
                        )
                        
                        self.combined_data.append({
                            'text': self.clean_text(row['text']),
                            'binary_label': binary_label,
                            'detailed_category': detailed_category,
                            'dataset': 'spam_parquet',
                            'source_file': str(parquet_file),
                            'data_type': 'text_classification',
                            'confidence': confidence,
                            'original_label': row['label'],
                            'original_type': 'text_spam'
                        })
                        
                        self.processing_stats['spam_parquet'] += 1
                        self.label_distribution[detailed_category] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {parquet_file}: {e}")
    
    def process_phishing_email_datasets(self):
        """Process phishing email datasets."""
        logger.info("Processing phishing email datasets...")
        
        phishing_dir = self.data_dir / "phishing email datasets"
        if not phishing_dir.exists():
            logger.warning("Phishing email datasets directory not found, skipping...")
            return
        
        for csv_file in phishing_dir.glob("*.csv"):
            try:
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(csv_file, encoding=encoding, low_memory=False)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    logger.warning(f"Could not decode {csv_file}, skipping...")
                    continue
                
                # Try to identify text and label columns
                text_cols = [col for col in df.columns if any(keyword in col.lower() 
                            for keyword in ['text', 'email', 'body', 'message', 'content', 'subject'])]
                label_cols = [col for col in df.columns if any(keyword in col.lower() 
                             for keyword in ['label', 'class', 'spam', 'phishing', 'target'])]
                
                if not text_cols:
                    text_cols = [df.columns[0]]
                if not label_cols and len(df.columns) > 1:
                    label_cols = [df.columns[-1]]
                
                if text_cols and label_cols:
                    text_col = text_cols[0]
                    label_col = label_cols[0]
                    
                    for _, row in df.iterrows():
                        if pd.notna(row.get(text_col)):
                            label_info = {
                                'label': row.get(label_col, 0),
                                'type': 'phishing',
                                'source_file': str(csv_file),
                                'dataset': f'phishing_{csv_file.stem}'
                            }
                            
                            detailed_category, binary_label, confidence = self.categorize_fraud_type(
                                label_info, f'phishing_{csv_file.stem}'
                            )
                            
                            self.combined_data.append({
                                'text': self.clean_text(row[text_col]),
                                'binary_label': binary_label,
                                'detailed_category': detailed_category,
                                'dataset': f'phishing_{csv_file.stem}',
                                'source_file': str(csv_file),
                                'data_type': 'email_classification',
                                'confidence': confidence,
                                'original_label': row.get(label_col),
                                'original_type': 'email'
                            })
                            
                            self.processing_stats[f'phishing_{csv_file.stem}'] += 1
                            self.label_distribution[detailed_category] += 1
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
                continue
    
    def process_popup_db(self):
        """Process PopupDB dataset."""
        logger.info("Processing PopupDB dataset...")
        
        popup_csv = self.data_dir / "PopupDB-Data-main" / "databases" / "PopupDB.csv"
        if popup_csv.exists():
            try:
                df = pd.read_csv(popup_csv)
                
                for _, row in df.iterrows():
                    # Combine relevant fields for text
                    text_parts = []
                    if pd.notna(row.get('Domain')):
                        text_parts.append(f"Domain: {row['Domain']}")
                    if pd.notna(row.get('Url')):
                        text_parts.append(f"URL: {row['Url']}")
                    if pd.notna(row.get('Number')):
                        text_parts.append(f"Phone: {row['Number']}")
                    
                    if text_parts:
                        self.combined_data.append({
                            'text': self.clean_text(' | '.join(text_parts)),
                            'binary_label': 1,  # PopupDB contains only malicious entries
                            'detailed_category': 'popup_scam',
                            'dataset': 'popupdb',
                            'source_file': str(popup_csv),
                            'data_type': 'popup_classification',
                            'confidence': 'high',
                            'original_label': 1,
                            'original_type': 'malicious_popup',
                            'domain': row.get('Domain', ''),
                            'country': row.get('Country', '')
                        })
                        
                        self.processing_stats['popupdb'] += 1
                        self.label_distribution['popup_scam'] += 1
                        
            except Exception as e:
                logger.error(f"Error processing PopupDB: {e}")
    
    def generate_corrected_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive statistics about the corrected dataset."""
        if not self.combined_data:
            return {}
        
        df = pd.DataFrame(self.combined_data)
        
        stats = {
            'total_samples': len(df),
            'fraud_samples': len(df[df['binary_label'] == 1]),
            'legitimate_samples': len(df[df['binary_label'] == 0]),
            'fraud_percentage': (len(df[df['binary_label'] == 1]) / len(df)) * 100,
            'datasets_count': df['dataset'].nunique(),
            'data_types': df['data_type'].value_counts().to_dict(),
            'average_text_length': float(df['text'].str.len().mean()),
            'empty_texts': int(df['text'].str.len().eq(0).sum()),
            
            # Corrected statistics
            'detailed_categories': df['detailed_category'].value_counts().to_dict(),
            'confidence_distribution': df['confidence'].value_counts().to_dict(),
            'processing_stats': dict(self.processing_stats),
            'correction_stats': dict(self.correction_stats),
            
            # Fraud-specific statistics (only for binary_label=1)
            'fraud_category_stats': {},
            'legitimate_vs_fraud_by_dataset': {}
        }
        
        # Fraud category statistics (only actual frauds)
        fraud_df = df[df['binary_label'] == 1]
        if len(fraud_df) > 0:
            for category in fraud_df['detailed_category'].unique():
                cat_df = fraud_df[fraud_df['detailed_category'] == category]
                stats['fraud_category_stats'][category] = {
                    'count': len(cat_df),
                    'percentage_of_fraud': len(cat_df) / len(fraud_df) * 100,
                    'avg_text_length': float(cat_df['text'].str.len().mean()),
                    'datasets': cat_df['dataset'].unique().tolist()
                }
        
        # Dataset breakdown
        for dataset in df['dataset'].unique():
            dataset_df = df[df['dataset'] == dataset]
            fraud_count = len(dataset_df[dataset_df['binary_label'] == 1])
            legit_count = len(dataset_df[dataset_df['binary_label'] == 0])
            
            stats['legitimate_vs_fraud_by_dataset'][dataset] = {
                'total_samples': len(dataset_df),
                'fraud_samples': fraud_count,
                'legitimate_samples': legit_count,
                'fraud_percentage': fraud_count / len(dataset_df) * 100 if len(dataset_df) > 0 else 0
            }
        
        return stats
    
    def save_corrected_dataset(self, output_path: str):
        """Save the corrected dataset."""
        if not self.combined_data:
            logger.error("No data to save. Please process datasets first.")
            return
        
        df = pd.DataFrame(self.combined_data)
        
        # Remove duplicates based on text content
        original_count = len(df)
        df = df.drop_duplicates(subset=['text'], keep='first')
        dedup_count = len(df)
        
        if original_count > dedup_count:
            logger.info(f"Removed {original_count - dedup_count} duplicate entries")
        
        # Sort by category and confidence for better organization
        df = df.sort_values(['detailed_category', 'confidence', 'dataset'])
        
        # Save to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Corrected dataset saved to {output_path}")
        logger.info(f"Final dataset size: {len(df)} samples")
        
        return df
    
    def process_all_datasets(self):
        """Process all available datasets with corrected categorization."""
        logger.info("Starting CORRECTED fraud detection dataset processing...")
        
        # Process each dataset type
        self.process_difraud_datasets()
        self.process_dialogue_datasets()
        self.process_spam_datasets()
        self.process_phishing_email_datasets()
        self.process_popup_db()
        
        logger.info(f"Processing complete. Total samples collected: {len(self.combined_data)}")
        
        # Print corrected category distribution
        logger.info("\\nCORRECTED Category distribution:")
        for category, count in sorted(self.label_distribution.items()):
            logger.info(f"  {category}: {count}")
        
        # Print correction stats
        if self.correction_stats:
            logger.info("\\nCorrection statistics:")
            for correction, count in sorted(self.correction_stats.items()):
                logger.info(f"  {correction}: {count}")


def main():
    """Main execution function."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path, default=Path('artifacts/corrected.csv'))
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; choose a new path')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data_directory = str(args.data_dir)
    output_file = str(args.output)

    # Initialize corrected processor
    processor = CorrectedFraudDataProcessor(data_directory)
    
    # Process all datasets
    processor.process_all_datasets()
    
    # Generate and display statistics
    stats = processor.generate_corrected_statistics()
    
    if stats:
        logger.info("\\n=== CORRECTED DATASET STATISTICS ===")
        logger.info(f"Total samples: {stats['total_samples']:,}")
        logger.info(f"Fraudulent samples: {stats['fraud_samples']:,} ({stats['fraud_percentage']:.1f}%)")
        logger.info(f"Legitimate samples: {stats['legitimate_samples']:,}")
        logger.info(f"Number of source datasets: {stats['datasets_count']}")
        logger.info(f"Average text length: {stats['average_text_length']:.1f} characters")
        
        logger.info(f"\\nFraud categories ({len([k for k in stats['detailed_categories'].keys() if k != 'legitimate'])} fraud types):")
        for category, count in sorted(stats['detailed_categories'].items(), key=lambda x: x[1], reverse=True):
            if category != 'legitimate':
                percentage = count / stats['fraud_samples'] * 100 if stats['fraud_samples'] > 0 else 0
                logger.info(f"  {category}: {count:,} samples ({percentage:.1f}% of fraud)")
        
        logger.info(f"\\nLegitimate samples: {stats['detailed_categories'].get('legitimate', 0):,}")
    
    # Save corrected dataset
    final_df = processor.save_corrected_dataset(output_file)
    
    if final_df is not None:
        # Recompute statistics after deduplication, matching the saved artifact.
        processor.combined_data = final_df.to_dict('records')
        stats = processor.generate_corrected_statistics()
        stats['statistics_stage'] = 'post_deduplication'
        # Save corrected metadata
        metadata_file = output_file.replace('.csv', '_metadata.json')
        with open(metadata_file, 'w') as f:
            # Convert numpy types to Python types for JSON serialization
            json_stats = {}
            for key, value in stats.items():
                if isinstance(value, dict):
                    json_stats[key] = {str(k): (int(v) if hasattr(v, 'item') else v) for k, v in value.items()}
                else:
                    json_stats[key] = int(value) if hasattr(value, 'item') else value
            json.dump(json_stats, f, indent=2, default=str)
        logger.info(f"Corrected metadata saved to {metadata_file}")
        
        # Create corrected category samples
        sample_file = output_file.replace('.csv', '_category_samples.csv')
        sample_dfs = []
        
        # Get samples from each fraud category
        fraud_categories = [cat for cat in final_df['detailed_category'].unique() if cat != 'legitimate']
        for category in ['legitimate'] + fraud_categories:
            cat_df = final_df[final_df['detailed_category'] == category]
            sample_count = min(3, len(cat_df))
            if sample_count > 0:
                sample_dfs.append(cat_df.head(sample_count))
        
        if sample_dfs:
            sample_df = pd.concat(sample_dfs, ignore_index=True)
            sample_df.to_csv(sample_file, index=False)
            logger.info(f"Corrected category samples saved to {sample_file}")
    
    logger.info("\\n=== CORRECTED PROCESSING COMPLETE ===")
    logger.info("The corrected fraud detection dataset is ready!")
    logger.info("Key corrections made:")
    logger.info("- Fixed misclassification of legitimate communications as scam types")
    logger.info("- Properly categorized actual fraud types only for label=1 cases")
    logger.info("- Separated legitimate appointment/delivery/insurance communications")
    logger.info("- Maintained accurate multi-class fraud categorization")


if __name__ == "__main__":
    main()
