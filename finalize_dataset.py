#!/usr/bin/env python3
"""
Clean and Finalize Streamlined Fraud Detection Dataset

This script fixes the one null text issue and creates the final clean dataset.
"""

import pandas as pd
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_and_finalize():
    """Clean the dataset and create final version."""
    
    input_file = "/Users/admin/Downloads/data/streamlined_fraud_detection_dataset.csv"
    output_file = "/Users/admin/Downloads/data/final_fraud_detection_dataset.csv"
    metadata_file = "/Users/admin/Downloads/data/final_fraud_detection_dataset_metadata.json"
    
    logger.info("Loading streamlined dataset...")
    df = pd.read_csv(input_file)
    
    logger.info(f"Original dataset: {len(df):,} samples")
    
    # Check for issues
    null_texts = df['text'].isnull().sum()
    empty_texts = (df['text'].str.strip() == '').sum()
    
    logger.info(f"Null texts found: {null_texts}")
    logger.info(f"Empty texts found: {empty_texts}")
    
    # Remove rows with null or empty text
    initial_size = len(df)
    df = df.dropna(subset=['text'])
    df = df[df['text'].str.strip() != '']
    
    removed_samples = initial_size - len(df)
    logger.info(f"Removed {removed_samples} samples with null/empty text")
    logger.info(f"Final dataset: {len(df):,} samples")
    
    # Verify data quality
    logger.info("\\n=== FINAL DATA QUALITY CHECK ===")
    logger.info(f"Null texts: {df['text'].isnull().sum()}")
    logger.info(f"Empty texts: {(df['text'].str.strip() == '').sum()}")
    logger.info(f"Invalid labels: {(~df['binary_label'].isin([0, 1])).sum()}")
    logger.info(f"Unique categories: {df['detailed_category'].nunique()}")
    logger.info(f"Unique data types: {df['data_type'].nunique()}")
    
    # Generate final statistics
    stats = {
        "total_samples": len(df),
        "fraud_samples": int((df['binary_label'] == 1).sum()),
        "legitimate_samples": int((df['binary_label'] == 0).sum()),
        "fraud_percentage": float(df['binary_label'].mean() * 100),
        "columns": list(df.columns),
        "detailed_categories": df['detailed_category'].value_counts().to_dict(),
        "data_types": df['data_type'].value_counts().to_dict(),
        "text_length_stats": {
            "mean": float(df['text'].str.len().mean()),
            "median": float(df['text'].str.len().median()),
            "min": int(df['text'].str.len().min()),
            "max": int(df['text'].str.len().max()),
            "std": float(df['text'].str.len().std())
        },
        "dataset_info": {
            "purpose": "NLP/LLM fraud detection training",
            "columns_description": {
                "text": "Main content to classify (required for training)",
                "binary_label": "Binary fraud label (0=legitimate, 1=fraud)",
                "detailed_category": "Multi-class fraud categories for specialized training",
                "data_type": "Content type for domain-specific analysis"
            },
            "removed_columns": [
                "source_file", "dataset", "confidence", "original_label", 
                "original_type", "domain", "country"
            ],
            "optimization": "Streamlined for machine learning training efficiency"
        }
    }
    
    # Display final statistics
    logger.info(f"\\n=== FINAL DATASET STATISTICS ===")
    logger.info(f"Total samples: {stats['total_samples']:,}")
    logger.info(f"Fraud samples: {stats['fraud_samples']:,} ({stats['fraud_percentage']:.1f}%)")
    logger.info(f"Legitimate samples: {stats['legitimate_samples']:,}")
    
    logger.info(f"\\nData type distribution:")
    for dtype, count in stats['data_types'].items():
        percentage = (count / stats['total_samples']) * 100
        logger.info(f"  {dtype}: {count:,} ({percentage:.1f}%)")
    
    logger.info(f"\\nFraud category distribution:")
    for category, count in stats['detailed_categories'].items():
        percentage = (count / stats['total_samples']) * 100
        logger.info(f"  {category}: {count:,} ({percentage:.1f}%)")
    
    logger.info(f"\\nText length statistics:")
    logger.info(f"  Mean: {stats['text_length_stats']['mean']:.0f} characters")
    logger.info(f"  Median: {stats['text_length_stats']['median']:.0f} characters")
    logger.info(f"  Range: {stats['text_length_stats']['min']}-{stats['text_length_stats']['max']} characters")
    
    # Save final dataset
    logger.info(f"\\nSaving final dataset to: {output_file}")
    df.to_csv(output_file, index=False)
    
    # Save metadata
    logger.info(f"Saving metadata to: {metadata_file}")
    with open(metadata_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Create sample file
    sample_file = "/Users/admin/Downloads/data/final_fraud_detection_dataset_sample.csv"
    sample_df = df.head(20)
    sample_df.to_csv(sample_file, index=False)
    logger.info(f"Sample file saved: {sample_file}")
    
    logger.info(f"\\n=== OPTIMIZATION COMPLETE ===")
    logger.info(f"🎉 Final fraud detection dataset ready for NLP/LLM training!")
    logger.info(f"\\n📊 Key improvements:")
    logger.info(f"   • Reduced from 11 to 4 essential columns (63.6% reduction)")
    logger.info(f"   • Removed irrelevant metadata columns")
    logger.info(f"   • Cleaned {removed_samples} problematic samples")
    logger.info(f"   • Optimized for machine learning efficiency")
    
    logger.info(f"\\n📁 Final files:")
    logger.info(f"   • final_fraud_detection_dataset.csv (main dataset)")
    logger.info(f"   • final_fraud_detection_dataset_metadata.json (statistics)")
    logger.info(f"   • final_fraud_detection_dataset_sample.csv (inspection sample)")
    
    return df, stats

if __name__ == "__main__":
    logger.info("=== FINALIZING FRAUD DETECTION DATASET ===")
    clean_and_finalize()
