#!/usr/bin/env python3
"""
Streamline Fraud Detection Dataset

This script removes irrelevant columns from the comprehensive fraud detection dataset,
keeping only the essential columns needed for training NLP/LLM fraud detection models.

Essential columns for NLP/LLM training:
1. text - The main content to classify (REQUIRED)
2. binary_label - 0/1 fraud label (REQUIRED)
3. detailed_category - Multi-class fraud categories (USEFUL for multi-class training)
4. data_type - Type of content (email, sms, dialogue, etc.) - USEFUL for domain analysis

Columns to REMOVE (not needed for NLP training):
- source_file - File path metadata (not relevant for training)
- dataset - Source dataset name (not needed for model training)
- confidence - All marked as "high" anyway
- original_label - Redundant with binary_label
- original_type - Redundant with detailed_category
- domain - Only relevant for popup data (small subset)
- country - Only relevant for popup data (small subset)
"""

import pandas as pd
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def streamline_dataset():
    """Streamline the fraud detection dataset by removing irrelevant columns."""
    
    # Input and output paths
    input_file = "/Users/admin/Downloads/data/corrected_fraud_detection_dataset.csv"
    output_file = "/Users/admin/Downloads/data/streamlined_fraud_detection_dataset.csv"
    metadata_file = "/Users/admin/Downloads/data/streamlined_fraud_detection_dataset_metadata.json"
    
    logger.info("Loading the comprehensive fraud detection dataset...")
    
    try:
        # Load the dataset in chunks to handle large file
        chunk_size = 10000
        chunks = []
        
        for chunk in pd.read_csv(input_file, chunksize=chunk_size):
            chunks.append(chunk)
        
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Dataset loaded: {len(df):,} samples")
        
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return
    
    # Display current columns
    logger.info(f"Current columns: {list(df.columns)}")
    
    # Define essential columns for NLP/LLM training
    essential_columns = [
        'text',                    # Main content (REQUIRED)
        'binary_label',           # 0/1 fraud label (REQUIRED)
        'detailed_category',      # Multi-class categories (USEFUL)
        'data_type'              # Content type for domain analysis (USEFUL)
    ]
    
    # Columns to remove (not needed for NLP training)
    columns_to_remove = [
        'source_file',           # File metadata - not relevant for training
        'dataset',               # Source dataset - not needed for model training
        'confidence',            # All marked as "high" - no variance
        'original_label',        # Redundant with binary_label
        'original_type',         # Redundant with detailed_category
        'domain',                # Only relevant for small popup subset
        'country'                # Only relevant for small popup subset
    ]
    
    logger.info(f"Keeping essential columns: {essential_columns}")
    logger.info(f"Removing irrelevant columns: {columns_to_remove}")
    
    # Create streamlined dataset
    streamlined_df = df[essential_columns].copy()
    
    # Verify no essential data is lost
    logger.info(f"Original dataset shape: {df.shape}")
    logger.info(f"Streamlined dataset shape: {streamlined_df.shape}")
    
    # Generate statistics for the streamlined dataset
    stats = {
        "total_samples": len(streamlined_df),
        "columns": list(streamlined_df.columns),
        "columns_removed": columns_to_remove,
        "fraud_samples": int((streamlined_df['binary_label'] == 1).sum()),
        "legitimate_samples": int((streamlined_df['binary_label'] == 0).sum()),
        "fraud_percentage": float(streamlined_df['binary_label'].mean() * 100),
        "detailed_categories": streamlined_df['detailed_category'].value_counts().to_dict(),
        "data_types": streamlined_df['data_type'].value_counts().to_dict(),
        "text_length_stats": {
            "mean": float(streamlined_df['text'].str.len().mean()),
            "median": float(streamlined_df['text'].str.len().median()),
            "min": int(streamlined_df['text'].str.len().min()),
            "max": int(streamlined_df['text'].str.len().max())
        },
        "memory_reduction": {
            "original_columns": len(df.columns),
            "streamlined_columns": len(streamlined_df.columns),
            "columns_reduced": len(df.columns) - len(streamlined_df.columns),
            "reduction_percentage": round((1 - len(streamlined_df.columns) / len(df.columns)) * 100, 1)
        }
    }
    
    # Display key statistics
    logger.info(f"\\n=== STREAMLINED DATASET STATISTICS ===")
    logger.info(f"Total samples: {stats['total_samples']:,}")
    logger.info(f"Fraud samples: {stats['fraud_samples']:,} ({stats['fraud_percentage']:.1f}%)")
    logger.info(f"Legitimate samples: {stats['legitimate_samples']:,}")
    logger.info(f"Columns reduced from {stats['memory_reduction']['original_columns']} to {stats['memory_reduction']['streamlined_columns']} ({stats['memory_reduction']['reduction_percentage']}% reduction)")
    
    logger.info(f"\\nData type distribution:")
    for dtype, count in stats['data_types'].items():
        logger.info(f"  {dtype}: {count:,}")
    
    logger.info(f"\\nDetailed category distribution:")
    for category, count in stats['detailed_categories'].items():
        logger.info(f"  {category}: {count:,}")
    
    # Save streamlined dataset
    logger.info(f"\\nSaving streamlined dataset to: {output_file}")
    streamlined_df.to_csv(output_file, index=False)
    
    # Save metadata
    logger.info(f"Saving metadata to: {metadata_file}")
    with open(metadata_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Create a sample file for inspection
    sample_file = "/Users/admin/Downloads/data/streamlined_fraud_detection_dataset_sample.csv"
    sample_df = streamlined_df.head(100)
    sample_df.to_csv(sample_file, index=False)
    logger.info(f"Sample file saved: {sample_file}")
    
    logger.info(f"\\n=== STREAMLINING COMPLETE ===")
    logger.info(f"✅ Dataset optimized for NLP/LLM training")
    logger.info(f"✅ Removed {len(columns_to_remove)} irrelevant columns")
    logger.info(f"✅ Kept {len(essential_columns)} essential columns")
    logger.info(f"✅ Ready for fraud detection model training")
    
    return streamlined_df, stats

def validate_streamlined_dataset():
    """Validate the streamlined dataset."""
    
    streamlined_file = "/Users/admin/Downloads/data/streamlined_fraud_detection_dataset.csv"
    
    if not Path(streamlined_file).exists():
        logger.error(f"Streamlined dataset not found: {streamlined_file}")
        return
    
    logger.info("\\n=== VALIDATION ===")
    
    # Load and validate
    df = pd.read_csv(streamlined_file)
    
    # Check essential columns exist
    required_columns = ['text', 'binary_label', 'detailed_category', 'data_type']
    missing_columns = set(required_columns) - set(df.columns)
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    # Check data integrity
    null_text = df['text'].isnull().sum()
    invalid_labels = (~df['binary_label'].isin([0, 1])).sum()
    
    logger.info(f"✅ All required columns present: {required_columns}")
    logger.info(f"✅ Dataset shape: {df.shape}")
    logger.info(f"✅ Null texts: {null_text}")
    logger.info(f"✅ Invalid labels: {invalid_labels}")
    
    if null_text > 0 or invalid_labels > 0:
        logger.warning("Data quality issues detected!")
        return False
    
    logger.info("✅ Dataset validation passed!")
    return True

def main():
    """Main execution function."""
    logger.info("=== STREAMLINING FRAUD DETECTION DATASET ===")
    logger.info("Removing irrelevant columns for NLP/LLM training...")
    
    # Streamline the dataset
    streamlined_df, stats = streamline_dataset()
    
    # Validate the result
    if validate_streamlined_dataset():
        logger.info("\\n🎉 SUCCESS: Dataset successfully streamlined and validated!")
        logger.info("\\n📁 Output files:")
        logger.info("   • streamlined_fraud_detection_dataset.csv (main dataset)")
        logger.info("   • streamlined_fraud_detection_dataset_metadata.json (statistics)")
        logger.info("   • streamlined_fraud_detection_dataset_sample.csv (sample for inspection)")
        
        logger.info("\\n🚀 Ready for NLP/LLM fraud detection training!")
        logger.info("   Essential columns: text, binary_label, detailed_category, data_type")
        logger.info("   Removed metadata columns not needed for training")
    else:
        logger.error("❌ Validation failed. Please check the dataset.")

if __name__ == "__main__":
    main()
