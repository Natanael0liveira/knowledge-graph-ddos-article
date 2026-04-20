"""
CIC-DDoS2019 Dataset Loader for Layer 7 DDoS Detection Experiments
===================================================================

This module provides utilities for loading, preprocessing, and preparing
the CIC-DDoS2019 dataset for experimental evaluation of the Knowledge
Graph-based DDoS detection system.

Dataset Information:
- Source: Canadian Institute for Cybersecurity (CIC)
- URL: https://www.unb.ca/cic/datasets/ddos-2019.html
- Size: ~15 GB
- Attack Types: 12 (including HTTP Flood, DNS amplification, etc.)
- Features: 80+ network flow features

Reference:
Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2019).
"CIC-DDoS2019: A Comprehensive Dataset for DDoS Attack Detection."
IEEE Canadian Conference of Electrical and Computer Engineering (CCECE).

Author: [Your Name]
Paper: "Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks"
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, StratifiedKFold
import logging
from pathlib import Path
import pickle
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AttackType(Enum):
    """Attack types available in CIC-DDoS2019 dataset."""
    # Layer 7 Attacks
    HTTP_FLOOD = "HTTP_Flood"
    HTTPS_FLOOD = "HTTPS_Flood"
    DNS_AMPLIFICATION = "DNS_Amplification"
    NTP_AMPLIFICATION = "NTP_Amplification"
    SNMP_AMPLIFICATION = "SNMP_Amplification"
    SSDP_AMPLIFICATION = "SSDP_Amplification"
    UDP_FLOOD = "UDP_Flood"
    UDP_FRAGMENTATION = "UDP_Fragmentation"
    SYN_FLOOD = "Syn"
    SYN_FLOOD_2 = "Syn_DDoS"
    MSSQL = "MSSQL"
    LDAP = "LDAP"
    PORTSCAN = "PortScan"
    BENIGN = "Benign"


class Layer7AttackCategory(Enum):
    """Grouping of attacks relevant to Layer 7 DDoS detection."""
    APPLICATION_LAYER = "Application_Layer"  # HTTP_Flood, HTTPS_Flood
    DNS_BASED = "DNS_Based"  # DNS_Amplification
    AMPLIFICATION = "Amplification"  # NTP, SNMP, SSDP
    PROTOCOL_BASED = "Protocol_Based"  # SYN, UDP
    BENIGN = "Benign"


@dataclass
class DatasetConfig:
    """Configuration for dataset loading and preprocessing."""
    # Paths
    data_dir: str = "./data/CIC-DDoS2019"
    cache_dir: str = "./data/cache"
    
    # Preprocessing options
    normalize: bool = True
    remove_duplicates: bool = True
    handle_missing: str = "mean"  # "mean", "median", "drop", "zero"
    balance_strategy: str = "none"  # "none", "undersample", "oversample", "smote"
    
    # Feature selection
    feature_selection: str = "all"  # "all", "layer7", "custom"
    custom_features: List[str] = field(default_factory=list)
    
    # Split ratios
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # Random state for reproducibility
    random_state: int = 42
    
    # Sampling for large datasets
    sample_fraction: Optional[float] = None  # None for full dataset


@dataclass
class DatasetStatistics:
    """Statistics of the loaded dataset."""
    total_samples: int = 0
    num_features: int = 0
    num_classes: int = 0
    class_distribution: Dict[str, int] = field(default_factory=dict)
    missing_values: int = 0
    duplicate_rows: int = 0
    feature_types: Dict[str, str] = field(default_factory=dict)
    memory_usage_mb: float = 0.0


class CICDDoS2019Loader:
    """
    Loader for CIC-DDoS2019 dataset.
    
    This class handles:
    - Loading raw CSV files from the dataset
    - Preprocessing and feature engineering
    - Train/validation/test splitting
    - Caching processed data for faster subsequent loads
    
    Example:
        >>> config = DatasetConfig(data_dir="/path/to/CIC-DDoS2019")
        >>> loader = CICDDoS2019Loader(config)
        >>> X_train, X_val, X_test, y_train, y_val, y_test = loader.load()
    """
    
    # Layer 7 specific features
    LAYER7_FEATURES = [
        # Flow features
        'Flow Duration', 'Total Fwd Packets', 'Total Bwd Packets',
        'Flow Bytes/s', 'Flow Packets/s',
        
        # Packet statistics
        'Fwd Packet Length Max', 'Fwd Packet Length Min', 
        'Fwd Packet Length Mean', 'Fwd Packet Length Std',
        'Bwd Packet Length Max', 'Bwd Packet Length Min',
        'Bwd Packet Length Mean', 'Bwd Packet Length Std',
        
        # Timing features
        'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min',
        'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min',
        'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min',
        
        # Flags (important for attack detection)
        'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count',
        'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count',
        'ECE Flag Count', 'CWE Flag Count',
        
        # Packet counts
        'Down/Up Ratio', 'Average Packet Size',
        'Fwd Segment Size Avg', 'Bwd Segment Size Avg',
        
        # HTTP-specific (if available)
        'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
        
        # Subflow features
        'Subflow Fwd Packets', 'Subflow Fwd Bytes',
        'Subflow Bwd Packets', 'Subflow Bwd Bytes',
        
        # Bulk features (for application layer)
        'Fwd Bulk Rate Avg', 'Bwd Bulk Rate Avg',
        'Fwd Packets/s', 'Bwd Packets/s',
        
        # Window features
        'Init_Fwd_Win_Byts', 'Init_Bwd_Win_Byts',
        'Fwd Act Data Pkts', 'Bwd Act Data Pkts',
        
        # Label
        'Label'
    ]
    
    # Features to exclude (non-numeric or identifiers)
    EXCLUDE_FEATURES = [
        'Flow ID', 'Source IP', 'Destination IP', 'Timestamp',
        'Source Port', 'Destination Port', 'Protocol',
        'Fwd Header Length.1',  # Duplicate column
        'Unnamed: 0'  # Index column if present
    ]
    
    def __init__(self, config: Optional[DatasetConfig] = None):
        """
        Initialize the dataset loader.
        
        Args:
            config: Dataset configuration. Uses defaults if None.
        """
        self.config = config or DatasetConfig()
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names: List[str] = []
        self.statistics = DatasetStatistics()
        self._is_fitted = False
        
        # Create cache directory
        os.makedirs(self.config.cache_dir, exist_ok=True)
    
    def load(self, attack_types: Optional[List[AttackType]] = None) -> Tuple[
        np.ndarray, np.ndarray, np.ndarray, 
        np.ndarray, np.ndarray, np.ndarray
    ]:
        """
        Load and preprocess the dataset.
        
        Args:
            attack_types: Specific attack types to load. Loads all if None.
        
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        logger.info("Loading CIC-DDoS2019 dataset...")
        
        # Check for cached data
        cache_path = self._get_cache_path(attack_types)
        if os.path.exists(cache_path):
            logger.info(f"Loading from cache: {cache_path}")
            return self._load_from_cache(cache_path)
        
        # Load raw data
        df = self._load_raw_data(attack_types)
        
        # Preprocess
        df = self._preprocess(df)
        
        # Calculate statistics
        self._calculate_statistics(df)
        
        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self._split_data(df)
        
        # Normalize
        if self.config.normalize:
            X_train, X_val, X_test = self._normalize_features(
                X_train, X_val, X_test
            )
        
        # Save to cache
        self._save_to_cache(
            cache_path, 
            X_train, X_val, X_test, 
            y_train, y_val, y_test
        )
        
        self._is_fitted = True
        logger.info("Dataset loading complete.")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def _load_raw_data(self, attack_types: Optional[List[AttackType]]) -> pd.DataFrame:
        """Load raw CSV files from the dataset directory."""
        data_dir = Path(self.config.data_dir)
        
        if not data_dir.exists():
            raise FileNotFoundError(
                f"Dataset directory not found: {data_dir}. "
                "Please download CIC-DDoS2019 from https://www.unb.ca/cic/datasets/ddos-2019.html"
            )
        
        # Find all CSV files
        csv_files = list(data_dir.glob("**/*.csv"))
        
        if not csv_files:
            raise FileNotFoundError(
                f"No CSV files found in {data_dir}"
            )
        
        logger.info(f"Found {len(csv_files)} CSV files")
        
        # Load and concatenate
        dfs = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, low_memory=False)
                
                # Filter by attack type if specified
                if attack_types and 'Label' in df.columns:
                    attack_labels = [at.value for at in attack_types]
                    df = df[df['Label'].isin(attack_labels)]
                
                dfs.append(df)
                logger.info(f"Loaded {csv_file.name}: {len(df)} samples")
                
            except Exception as e:
                logger.warning(f"Error loading {csv_file}: {e}")
                continue
        
        if not dfs:
            raise ValueError("No data loaded from CSV files")
        
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined dataset: {len(combined_df)} samples")
        
        # Sample if requested
        if self.config.sample_fraction and self.config.sample_fraction < 1.0:
            combined_df = combined_df.sample(
                frac=self.config.sample_fraction, 
                random_state=self.config.random_state
            )
            logger.info(f"Sampled {len(combined_df)} records")
        
        return combined_df
    
    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess the raw dataframe."""
        logger.info("Preprocessing data...")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Remove duplicates
        if self.config.remove_duplicates:
            before = len(df)
            df = df.drop_duplicates()
            self.statistics.duplicate_rows = before - len(df)
            logger.info(f"Removed {self.statistics.duplicate_rows} duplicate rows")
        
        # Handle missing values
        missing_before = df.isnull().sum().sum()
        self.statistics.missing_values = missing_before
        
        if missing_before > 0:
            logger.info(f"Handling {missing_before} missing values...")
            if self.config.handle_missing == "mean":
                df = df.fillna(df.mean(numeric_only=True))
            elif self.config.handle_missing == "median":
                df = df.fillna(df.median(numeric_only=True))
            elif self.config.handle_missing == "zero":
                df = df.fillna(0)
            elif self.config.handle_missing == "drop":
                df = df.dropna()
        
        # Handle infinite values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)
        
        # Select features
        if self.config.feature_selection == "layer7":
            available_features = [
                f for f in self.LAYER7_FEATURES 
                if f in df.columns
            ]
            df = df[available_features]
        elif self.config.feature_selection == "custom":
            features = self.config.custom_features + ['Label']
            available_features = [f for f in features if f in df.columns]
            df = df[available_features]
        
        # Remove non-numeric columns except Label
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'Label' in df.columns and 'Label' not in numeric_cols:
            numeric_cols.append('Label')
        df = df[numeric_cols]
        
        # Store feature names
        self.feature_names = [c for c in df.columns if c != 'Label']
        
        logger.info(f"Preprocessed data: {len(df)} samples, {len(self.feature_names)} features")
        
        return df
    
    def _split_data(self, df: pd.DataFrame) -> Tuple[
        np.ndarray, np.ndarray, np.ndarray,
        np.ndarray, np.ndarray, np.ndarray
    ]:
        """Split data into train, validation, and test sets."""
        logger.info("Splitting data...")
        
        X = df[self.feature_names].values
        y = df['Label'].values if 'Label' in df.columns else np.zeros(len(df))
        
        # Encode labels
        y = self.label_encoder.fit_transform(y)
        
        # First split: train vs (val + test)
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y,
            test_size=(1 - self.config.train_ratio),
            random_state=self.config.random_state,
            stratify=y
        )
        
        # Second split: val vs test
        val_ratio = self.config.val_ratio / (self.config.val_ratio + self.config.test_ratio)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp,
            test_size=(1 - val_ratio),
            random_state=self.config.random_state,
            stratify=y_temp
        )
        
        logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def _normalize_features(
        self, 
        X_train: np.ndarray, 
        X_val: np.ndarray, 
        X_test: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Normalize features using StandardScaler."""
        logger.info("Normalizing features...")
        
        X_train = self.scaler.fit_transform(X_train)
        X_val = self.scaler.transform(X_val)
        X_test = self.scaler.transform(X_test)
        
        return X_train, X_val, X_test
    
    def _calculate_statistics(self, df: pd.DataFrame) -> None:
        """Calculate and store dataset statistics."""
        self.statistics.total_samples = len(df)
        self.statistics.num_features = len(self.feature_names)
        
        if 'Label' in df.columns:
            self.statistics.num_classes = df['Label'].nunique()
            self.statistics.class_distribution = df['Label'].value_counts().to_dict()
        
        self.statistics.memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Log statistics
        logger.info(f"Dataset Statistics:")
        logger.info(f"  Total samples: {self.statistics.total_samples:,}")
        logger.info(f"  Features: {self.statistics.num_features}")
        logger.info(f"  Classes: {self.statistics.num_classes}")
        logger.info(f"  Memory: {self.statistics.memory_usage_mb:.2f} MB")
        logger.info(f"  Class distribution:")
        for label, count in self.statistics.class_distribution.items():
            logger.info(f"    {label}: {count:,} ({count/self.statistics.total_samples*100:.2f}%)")
    
    def _get_cache_path(self, attack_types: Optional[List[AttackType]]) -> str:
        """Generate cache file path based on configuration."""
        config_hash = hash((
            str(attack_types),
            self.config.normalize,
            self.config.feature_selection,
            self.config.train_ratio,
            self.config.sample_fraction
        ))
        return os.path.join(
            self.config.cache_dir, 
            f"cic_ddos2019_{abs(config_hash)}.pkl"
        )
    
    def _save_to_cache(
        self, 
        path: str,
        X_train: np.ndarray, X_val: np.ndarray, X_test: np.ndarray,
        y_train: np.ndarray, y_val: np.ndarray, y_test: np.ndarray
    ) -> None:
        """Save processed data to cache."""
        cache_data = {
            'X_train': X_train, 'X_val': X_val, 'X_test': X_test,
            'y_train': y_train, 'y_val': y_val, 'y_test': y_test,
            'feature_names': self.feature_names,
            'statistics': self.statistics,
            'config': self.config
        }
        with open(path, 'wb') as f:
            pickle.dump(cache_data, f)
        logger.info(f"Saved to cache: {path}")
    
    def _load_from_cache(self, path: str) -> Tuple[
        np.ndarray, np.ndarray, np.ndarray,
        np.ndarray, np.ndarray, np.ndarray
    ]:
        """Load processed data from cache."""
        with open(path, 'rb') as f:
            cache_data = pickle.load(f)
        
        self.feature_names = cache_data['feature_names']
        self.statistics = cache_data['statistics']
        self._is_fitted = True
        
        return (
            cache_data['X_train'], cache_data['X_val'], cache_data['X_test'],
            cache_data['y_train'], cache_data['y_val'], cache_data['y_test']
        )
    
    def get_feature_names(self) -> List[str]:
        """Get the list of feature names."""
        return self.feature_names
    
    def get_class_names(self) -> List[str]:
        """Get the list of class names."""
        return list(self.label_encoder.classes_)
    
    def get_statistics(self) -> DatasetStatistics:
        """Get dataset statistics."""
        return self.statistics
    
    def get_cross_validation_folds(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        n_splits: int = 10
    ):
        """
        Generate stratified k-fold cross-validation splits.
        
        Args:
            X: Feature matrix
            y: Labels
            n_splits: Number of folds
        
        Yields:
            Tuple of (train_index, test_index) for each fold
        """
        skf = StratifiedKFold(
            n_splits=n_splits, 
            shuffle=True, 
            random_state=self.config.random_state
        )
        return skf.split(X, y)


class Layer7FeatureExtractor:
    """
    Extract Layer 7 specific features from network flow data.
    
    This class provides methods to compute features that are particularly
    relevant for detecting application-layer DDoS attacks.
    """
    
    @staticmethod
    def compute_request_rate_features(df: pd.DataFrame) -> pd.DataFrame:
        """Compute request rate features for HTTP flood detection."""
        features = pd.DataFrame()
        
        # Requests per second
        if 'Flow Duration' in df.columns and 'Total Fwd Packets' in df.columns:
            duration_sec = df['Flow Duration'] / 1_000_000  # Convert to seconds
            features['requests_per_second'] = df['Total Fwd Packets'] / duration_sec.clip(lower=1)
        
        # Burst ratio
        if 'Flow Packets/s' in df.columns:
            features['burst_ratio'] = df['Flow Packets/s'] / df['Flow Packets/s'].mean()
        
        return features
    
    @staticmethod
    def compute_session_features(df: pd.DataFrame) -> pd.DataFrame:
        """Compute session-based features for bot detection."""
        features = pd.DataFrame()
        
        # Packet size variance (low variance indicates automation)
        if all(col in df.columns for col in ['Fwd Packet Length Mean', 'Fwd Packet Length Std']):
            features['packet_size_cv'] = df['Fwd Packet Length Std'] / df['Fwd Packet Length Mean'].clip(lower=1)
        
        # Inter-arrival time regularity
        if all(col in df.columns for col in ['Flow IAT Mean', 'Flow IAT Std']):
            features['iat_cv'] = df['Flow IAT Std'] / df['Flow IAT Mean'].clip(lower=1)
        
        return features
    
    @staticmethod
    def compute_flag_features(df: pd.DataFrame) -> pd.DataFrame:
        """Compute flag-based features for attack pattern detection."""
        features = pd.DataFrame()
        
        flag_cols = ['SYN Flag Count', 'ACK Flag Count', 'RST Flag Count', 
                     'PSH Flag Count', 'FIN Flag Count']
        
        if all(col in df.columns for col in flag_cols):
            # Flag combinations
            features['syn_ack_ratio'] = df['SYN Flag Count'] / (df['ACK Flag Count'] + 1)
            features['flag_diversity'] = df[flag_cols].gt(0).sum(axis=1)
            
            # Suspicious flag patterns
            features['syn_only'] = ((df['SYN Flag Count'] > 0) & 
                                    (df['ACK Flag Count'] == 0)).astype(int)
        
        return features
    
    @staticmethod
    def compute_all_layer7_features(df: pd.DataFrame) -> pd.DataFrame:
        """Compute all Layer 7 specific features."""
        request_features = Layer7FeatureExtractor.compute_request_rate_features(df)
        session_features = Layer7FeatureExtractor.compute_session_features(df)
        flag_features = Layer7FeatureExtractor.compute_flag_features(df)
        
        return pd.concat([request_features, session_features, flag_features], axis=1)


def create_synthetic_layer7_data(
    n_samples: int = 10000,
    n_features: int = 50,
    attack_ratio: float = 0.3,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Create synthetic Layer 7 DDoS data for testing purposes.
    
    This function generates synthetic data that mimics the characteristics
    of Layer 7 DDoS attacks for initial development and testing.
    
    Args:
        n_samples: Number of samples to generate
        n_features: Number of features
        attack_ratio: Ratio of attack samples
        random_state: Random seed
    
    Returns:
        Tuple of (features DataFrame, labels Series)
    """
    np.random.seed(random_state)
    
    n_attacks = int(n_samples * attack_ratio)
    n_benign = n_samples - n_attacks
    
    # Generate benign traffic (normal distribution)
    benign_data = np.random.normal(0, 1, (n_benign, n_features))
    
    # Generate attack traffic (different distribution)
    # HTTP Flood: high request rate, low variance
    attack_data = np.random.normal(2, 0.5, (n_attacks, n_features))
    
    # Add attack-specific patterns
    attack_data[:, 0] *= 3  # Higher flow duration
    attack_data[:, 1] *= 5  # More packets
    attack_data[:, 4] *= 4  # Higher packet rate
    
    # Combine
    X = np.vstack([benign_data, attack_data])
    y = np.array(['Benign'] * n_benign + ['HTTP_Flood'] * n_attacks)
    
    # Shuffle
    indices = np.random.permutation(n_samples)
    X = X[indices]
    y = y[indices]
    
    # Create DataFrame
    feature_names = [f'feature_{i}' for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names)
    labels = pd.Series(y, name='Label')
    
    return df, labels


if __name__ == "__main__":
    # Example usage
    print("CIC-DDoS2019 Dataset Loader")
    print("=" * 50)
    
    # Create synthetic data for testing
    print("\nCreating synthetic Layer 7 DDoS data...")
    df, labels = create_synthetic_layer7_data(n_samples=1000)
    print(f"Generated {len(df)} samples with {len(df.columns)} features")
    print(f"Class distribution:\n{labels.value_counts()}")
    
    # Test loader with synthetic data
    print("\nTesting dataset loader...")
    config = DatasetConfig(
        data_dir="./data/synthetic",
        sample_fraction=1.0
    )
    
    # Save synthetic data for testing
    os.makedirs("./data/synthetic", exist_ok=True)
    df_with_label = df.copy()
    df_with_label['Label'] = labels
    df_with_label.to_csv("./data/synthetic/test_data.csv", index=False)
    
    # Load and process
    loader = CICDDoS2019Loader(config)
    try:
        X_train, X_val, X_test, y_train, y_val, y_test = loader.load()
        print(f"\nData loaded successfully:")
        print(f"  Train: {X_train.shape}")
        print(f"  Val: {X_val.shape}")
        print(f"  Test: {X_test.shape}")
        print(f"  Classes: {loader.get_class_names()}")
    except Exception as e:
        print(f"Error: {e}")
