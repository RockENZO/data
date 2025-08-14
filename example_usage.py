#!/usr/bin/env python3
"""
Example Usage Script for Comprehensive Fraud Detection Dataset

This script demonstrates how to load and use the combined fraud detection dataset
for training machine learning models. It includes examples for basic classification,
cross-domain evaluation, and performance analysis.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

class FraudDetectionExample:
    """Example class for demonstrating fraud detection dataset usage."""
    
    def __init__(self, dataset_path="combined_fraud_detection_dataset.csv"):
        """Initialize with dataset path."""
        self.dataset_path = dataset_path
        self.df = None
        self.models = {}
        
    def load_dataset(self):
        """Load the combined fraud detection dataset."""
        print("Loading dataset...")
        self.df = pd.read_csv(self.dataset_path)
        print(f"Dataset loaded: {self.df.shape[0]} samples, {self.df.shape[1]} features")
        return self.df
    
    def explore_dataset(self):
        """Explore the dataset structure and statistics."""
        print("\n=== DATASET EXPLORATION ===")
        
        # Basic statistics
        print(f"Total samples: {len(self.df):,}")
        print(f"Fraudulent samples: {(self.df['label'] == 1).sum():,} ({(self.df['label'] == 1).mean():.1%})")
        print(f"Legitimate samples: {(self.df['label'] == 0).sum():,} ({(self.df['label'] == 0).mean():.1%})")
        
        # Data type distribution
        print(f"\nData type distribution:")
        for dtype, count in self.df['data_type'].value_counts().items():
            fraud_rate = self.df[self.df['data_type'] == dtype]['label'].mean()
            print(f"  {dtype}: {count:,} samples ({fraud_rate:.1%} fraud rate)")
        
        # Text length statistics
        text_lengths = self.df['text'].str.len()
        print(f"\nText length statistics:")
        print(f"  Mean: {text_lengths.mean():.1f} characters")
        print(f"  Median: {text_lengths.median():.1f} characters")
        print(f"  Min: {text_lengths.min()} characters")
        print(f"  Max: {text_lengths.max()} characters")
        
        # Dataset source distribution
        print(f"\nTop 10 source datasets:")
        for dataset, count in self.df['dataset'].value_counts().head(10).items():
            print(f"  {dataset}: {count:,} samples")
    
    def create_sample_dataset(self, sample_size=10000):
        """Create a smaller sample for faster experimentation."""
        print(f"\nCreating sample dataset of {sample_size} samples...")
        
        # Stratified sampling to maintain label balance across data types
        sample_dfs = []
        for data_type in self.df['data_type'].unique():
            type_df = self.df[self.df['data_type'] == data_type]
            type_sample_size = int(sample_size * len(type_df) / len(self.df))
            
            if type_sample_size > 0:
                if len(type_df) <= type_sample_size:
                    sample_dfs.append(type_df)
                else:
                    type_sample = type_df.groupby('label', group_keys=False).apply(
                        lambda x: x.sample(min(len(x), type_sample_size // 2))
                    )
                    sample_dfs.append(type_sample)
        
        sample_df = pd.concat(sample_dfs, ignore_index=True)
        print(f"Sample created: {len(sample_df)} samples")
        print(f"Sample fraud rate: {sample_df['label'].mean():.1%}")
        
        return sample_df
    
    def train_basic_models(self, use_sample=True, sample_size=10000):
        """Train basic fraud detection models."""
        print("\n=== TRAINING BASIC MODELS ===")
        
        # Use sample or full dataset
        if use_sample:
            df = self.create_sample_dataset(sample_size)
        else:
            df = self.df
        
        # Prepare data
        X = df['text']
        y = df['label']
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Define models with pipelines
        models = {
            'Logistic Regression': Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, stop_words='english')),
                ('classifier', LogisticRegression(random_state=42))
            ]),
            'Random Forest': Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, stop_words='english')),
                ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
        }
        
        # Train and evaluate models
        results = {}
        for name, model in models.items():
            print(f"\nTraining {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Metrics
            auc = roc_auc_score(y_test, y_pred_proba)
            
            print(f"{name} Results:")
            print(f"  AUC-ROC: {auc:.4f}")
            print(f"  Classification Report:")
            print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))
            
            # Store results
            results[name] = {
                'model': model,
                'auc': auc,
                'predictions': y_pred,
                'probabilities': y_pred_proba
            }
            self.models[name] = model
        
        return results, X_test, y_test
    
    def cross_domain_evaluation(self, use_sample=True):
        """Evaluate model performance across different data types."""
        print("\n=== CROSS-DOMAIN EVALUATION ===")
        
        if use_sample:
            df = self.create_sample_dataset(5000)  # Smaller sample for cross-domain
        else:
            df = self.df
        
        # Get data types with sufficient samples
        data_types = df['data_type'].value_counts()
        valid_types = data_types[data_types >= 100].index.tolist()
        
        print(f"Evaluating across {len(valid_types)} data types: {valid_types}")
        
        # Cross-domain results matrix
        results_matrix = pd.DataFrame(index=valid_types, columns=valid_types)
        
        for train_type in valid_types:
            train_df = df[df['data_type'] == train_type]
            X_train = train_df['text']
            y_train = train_df['label']
            
            # Skip if not enough samples or no class diversity
            if len(train_df) < 50 or len(train_df['label'].unique()) < 2:
                continue
            
            # Train model
            model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=2000, stop_words='english')),
                ('classifier', LogisticRegression(random_state=42))
            ])
            
            try:
                model.fit(X_train, y_train)
                
                for test_type in valid_types:
                    test_df = df[df['data_type'] == test_type]
                    
                    if len(test_df) < 20 or len(test_df['label'].unique()) < 2:
                        continue
                    
                    X_test = test_df['text']
                    y_test = test_df['label']
                    
                    # Evaluate
                    y_pred_proba = model.predict_proba(X_test)[:, 1]
                    auc = roc_auc_score(y_test, y_pred_proba)
                    results_matrix.loc[train_type, test_type] = auc
                    
            except Exception as e:
                print(f"Error training on {train_type}: {e}")
                continue
        
        # Display results
        print("\nCross-domain AUC matrix (rows=train, cols=test):")
        print(results_matrix.fillna(0).round(3))
        
        return results_matrix
    
    def analyze_fraud_patterns(self):
        """Analyze patterns in fraudulent vs legitimate content."""
        print("\n=== FRAUD PATTERN ANALYSIS ===")
        
        fraud_texts = self.df[self.df['label'] == 1]['text']
        legit_texts = self.df[self.df['label'] == 0]['text']
        
        # Text length comparison
        fraud_lengths = fraud_texts.str.len()
        legit_lengths = legit_texts.str.len()
        
        print(f"Text length comparison:")
        print(f"  Fraud mean length: {fraud_lengths.mean():.1f} characters")
        print(f"  Legitimate mean length: {legit_lengths.mean():.1f} characters")
        
        # Common words analysis (simple approach)
        from collections import Counter
        import re
        
        def get_words(texts, min_length=3):
            words = []
            for text in texts.head(1000):  # Sample for efficiency
                if pd.notna(text):
                    words.extend(re.findall(r'\b[a-zA-Z]{%d,}\b' % min_length, text.lower()))
            return Counter(words)
        
        fraud_words = get_words(fraud_texts)
        legit_words = get_words(legit_texts)
        
        print(f"\nTop 10 words in fraud content:")
        for word, count in fraud_words.most_common(10):
            print(f"  {word}: {count}")
        
        print(f"\nTop 10 words in legitimate content:")
        for word, count in legit_words.most_common(10):
            print(f"  {word}: {count}")
    
    def demonstrate_model_usage(self):
        """Demonstrate how to use trained models for prediction."""
        print("\n=== MODEL USAGE DEMONSTRATION ===")
        
        if not self.models:
            print("No models trained yet. Training a simple model...")
            self.train_basic_models(use_sample=True, sample_size=5000)
        
        # Get a trained model
        model = list(self.models.values())[0]
        
        # Example texts to classify
        example_texts = [
            "Congratulations! You've won $1000! Click here to claim your prize!",
            "Meeting scheduled for tomorrow at 3 PM in conference room A.",
            "URGENT! Your account will be suspended unless you verify immediately!",
            "Thank you for your purchase. Your order will be shipped within 2 business days.",
            "You have been selected for a special offer. Call now to claim!"
        ]
        
        print("Classifying example texts:")
        for i, text in enumerate(example_texts, 1):
            prediction = model.predict([text])[0]
            probability = model.predict_proba([text])[0, 1]
            
            label = "FRAUD" if prediction == 1 else "LEGITIMATE"
            print(f"\n{i}. Text: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
            print(f"   Prediction: {label} (confidence: {probability:.3f})")


def main():
    """Main execution function."""
    print("=== FRAUD DETECTION DATASET EXAMPLE ===")
    
    # Initialize example class
    example = FraudDetectionExample()
    
    # Load and explore dataset
    example.load_dataset()
    example.explore_dataset()
    
    # Train basic models
    results, X_test, y_test = example.train_basic_models(use_sample=True, sample_size=10000)
    
    # Cross-domain evaluation (optional - can be slow)
    print("\nSkipping cross-domain evaluation (can be slow). Set use_sample=False for full evaluation.")
    # example.cross_domain_evaluation(use_sample=True)
    
    # Analyze fraud patterns
    example.analyze_fraud_patterns()
    
    # Demonstrate model usage
    example.demonstrate_model_usage()
    
    print("\n=== EXAMPLE COMPLETE ===")
    print("This example demonstrates basic usage of the fraud detection dataset.")
    print("For production use, consider:")
    print("- Using the full dataset (not just samples)")
    print("- More sophisticated feature engineering")
    print("- Deep learning models (BERT, etc.)")
    print("- Cross-validation and hyperparameter tuning")
    print("- Ensemble methods")


if __name__ == "__main__":
    main()
