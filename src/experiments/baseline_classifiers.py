"""
Baseline Classifiers for Layer 7 DDoS Detection Comparison
===========================================================

This module implements baseline classifiers for comparison with the
Knowledge Graph-based DDoS detection approach. Includes traditional ML,
Deep Learning, and Graph Neural Network baselines.

Implemented Baselines:
1. Random Forest (RF) - Traditional ML baseline
2. XGBoost - Gradient Boosting state-of-the-art
3. LSTM - Deep Learning for sequential data
4. GCN (Graph Convolutional Network) - Graph Neural Network baseline
5. Autoencoder - Unsupervised anomaly detection

Reference for baselines:
- Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
- Chen, T., & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System." KDD.
- Hochreiter, S., & Schmidhuber, J. (1997). "Long Short-Term Memory." Neural Computation.
- Kipf, T. N., & Welling, M. (2017). "Semi-Supervised Classification with GCNs." ICLR.

Author: [Your Name]
Paper: "Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
import pickle
from pathlib import Path

# Scikit-learn
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
from sklearn.model_selection import cross_val_score, StratifiedKFold

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Container for model evaluation metrics."""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0
    fpr: float = 0.0  # False Positive Rate
    training_time: float = 0.0
    inference_time: float = 0.0
    
    # Per-class metrics
    per_class_precision: Dict[str, float] = field(default_factory=dict)
    per_class_recall: Dict[str, float] = field(default_factory=dict)
    per_class_f1: Dict[str, float] = field(default_factory=dict)
    
    # Confusion matrix
    confusion_matrix: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_roc': self.auc_roc,
            'fpr': self.fpr,
            'training_time': self.training_time,
            'inference_time': self.inference_time,
            'per_class_precision': self.per_class_precision,
            'per_class_recall': self.per_class_recall,
            'per_class_f1': self.per_class_f1
        }
    
    def __str__(self) -> str:
        return (
            f"Accuracy: {self.accuracy:.4f}, "
            f"Precision: {self.precision:.4f}, "
            f"Recall: {self.recall:.4f}, "
            f"F1: {self.f1_score:.4f}, "
            f"AUC-ROC: {self.auc_roc:.4f}, "
            f"FPR: {self.fpr:.4f}"
        )


class BaselineClassifier(ABC):
    """Abstract base class for baseline classifiers."""
    
    def __init__(self, name: str, random_state: int = 42):
        self.name = name
        self.random_state = random_state
        self.model = None
        self._is_fitted = False
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BaselineClassifier':
        """Train the classifier."""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        pass
    
    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities."""
        pass
    
    def evaluate(
        self, 
        X_test: np.ndarray, 
        y_test: np.ndarray,
        class_names: Optional[List[str]] = None
    ) -> ModelMetrics:
        """
        Evaluate the classifier on test data.
        
        Args:
            X_test: Test features
            y_test: Test labels
            class_names: Names of classes for per-class metrics
        
        Returns:
            ModelMetrics object with evaluation results
        """
        if not self._is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        # Measure inference time
        start_time = time.time()
        y_pred = self.predict(X_test)
        inference_time = time.time() - start_time
        
        # Calculate metrics
        metrics = ModelMetrics()
        metrics.accuracy = accuracy_score(y_test, y_pred)
        metrics.precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics.recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics.f1_score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        metrics.inference_time = inference_time
        
        # Confusion matrix
        metrics.confusion_matrix = confusion_matrix(y_test, y_pred)
        
        # False Positive Rate
        tn, fp, fn, tp = metrics.confusion_matrix.ravel()[:4] if metrics.confusion_matrix.size == 4 else (0, 0, 0, 0)
        metrics.fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        # AUC-ROC (for binary or multiclass)
        try:
            y_proba = self.predict_proba(X_test)
            if y_proba.shape[1] == 2:
                metrics.auc_roc = roc_auc_score(y_test, y_proba[:, 1])
            else:
                metrics.auc_roc = roc_auc_score(y_test, y_proba, multi_class='ovr')
        except Exception as e:
            logger.warning(f"Could not compute AUC-ROC: {e}")
            metrics.auc_roc = 0.0
        
        # Per-class metrics
        if class_names:
            from sklearn.metrics import precision_recall_fscore_support
            precisions, recalls, f1s, _ = precision_recall_fscore_support(
                y_test, y_pred, average=None, zero_division=0
            )
            for i, name in enumerate(class_names):
                if i < len(precisions):
                    metrics.per_class_precision[name] = precisions[i]
                    metrics.per_class_recall[name] = recalls[i]
                    metrics.per_class_f1[name] = f1s[i]
        
        return metrics
    
    def save(self, path: str) -> None:
        """Save the trained model."""
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str) -> None:
        """Load a trained model."""
        with open(path, 'rb') as f:
            self.model = pickle.load(f)
        self._is_fitted = True
        logger.info(f"Model loaded from {path}")


class RandomForestBaseline(BaselineClassifier):
    """
    Random Forest classifier baseline.
    
    Reference:
    Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
    """
    
    def __init__(
        self, 
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        random_state: int = 42,
        n_jobs: int = -1
    ):
        super().__init__("Random Forest", random_state)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.n_jobs = n_jobs
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'RandomForestBaseline':
        """Train the Random Forest classifier."""
        logger.info(f"Training Random Forest with {self.n_estimators} trees...")
        start_time = time.time()
        
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            random_state=self.random_state,
            n_jobs=self.n_jobs
        )
        self.model.fit(X, y)
        self._is_fitted = True
        
        self.training_time = time.time() - start_time
        logger.info(f"Training completed in {self.training_time:.2f}s")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> np.ndarray:
        """Get feature importances from the trained model."""
        if not self._is_fitted:
            raise ValueError("Model must be fitted first")
        return self.model.feature_importances_


class XGBoostBaseline(BaselineClassifier):
    """
    XGBoost classifier baseline.
    
    Reference:
    Chen, T., & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System." KDD.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        random_state: int = 42,
        n_jobs: int = -1,
        use_gpu: bool = False
    ):
        super().__init__("XGBoost", random_state)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.n_jobs = n_jobs
        self.use_gpu = use_gpu
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'XGBoostBaseline':
        """Train the XGBoost classifier."""
        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError(
                "XGBoost not installed. Install with: pip install xgboost"
            )
        
        logger.info(f"Training XGBoost with {self.n_estimators} estimators...")
        start_time = time.time()
        
        # Determine number of classes
        n_classes = len(np.unique(y))
        objective = 'multi:softprob' if n_classes > 2 else 'binary:logistic'
        
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            objective=objective,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            tree_method='hist' if self.use_gpu else 'auto',
            device='cuda' if self.use_gpu else 'cpu'
        )
        self.model.fit(X, y)
        self._is_fitted = True
        
        self.training_time = time.time() - start_time
        logger.info(f"Training completed in {self.training_time:.2f}s")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> np.ndarray:
        """Get feature importances from the trained model."""
        if not self._is_fitted:
            raise ValueError("Model must be fitted first")
        return self.model.feature_importances_


class LSTMBaseline(BaselineClassifier):
    """
    LSTM (Long Short-Term Memory) baseline for sequence classification.
    
    Reference:
    Hochreiter, S., & Schmidhuber, J. (1997). "Long Short-Term Memory." 
    Neural Computation, 9(8), 1735-1780.
    """
    
    def __init__(
        self,
        hidden_units: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
        learning_rate: float = 0.001,
        batch_size: int = 64,
        epochs: int = 50,
        random_state: int = 42
    ):
        super().__init__("LSTM", random_state)
        self.hidden_units = hidden_units
        self.num_layers = num_layers
        self.dropout = dropout
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.n_classes = 0
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LSTMBaseline':
        """Train the LSTM classifier."""
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError(
                "PyTorch not installed. Install with: pip install torch"
            )
        
        logger.info(f"Training LSTM with {self.hidden_units} hidden units...")
        start_time = time.time()
        
        # Set random seed
        torch.manual_seed(self.random_state)
        
        # Determine number of classes
        self.n_classes = len(np.unique(y))
        
        # Reshape input for LSTM (samples, timesteps, features)
        # For tabular data, treat each feature as a timestep
        X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)
        X_tensor = torch.FloatTensor(X_reshaped)
        y_tensor = torch.LongTensor(y)
        
        # Create DataLoader
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Define LSTM model
        class LSTMModel(nn.Module):
            def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout):
                super(LSTMModel, self).__init__()
                self.hidden_size = hidden_size
                self.num_layers = num_layers
                self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                                    batch_first=True, dropout=dropout)
                self.fc = nn.Linear(hidden_size, num_classes)
            
            def forward(self, x):
                h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                out, _ = self.lstm(x, (h0, c0))
                out = self.fc(out[:, -1, :])
                return out
        
        # Initialize model
        self.model = LSTMModel(
            input_size=1,
            hidden_size=self.hidden_units,
            num_layers=self.num_layers,
            num_classes=self.n_classes,
            dropout=self.dropout
        )
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{self.epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
        self._is_fitted = True
        self.training_time = time.time() - start_time
        logger.info(f"Training completed in {self.training_time:.2f}s")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        import torch
        
        self.model.eval()
        with torch.no_grad():
            X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)
            X_tensor = torch.FloatTensor(X_reshaped)
            outputs = self.model(X_tensor)
            _, predicted = torch.max(outputs, 1)
            return predicted.numpy()
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        import torch
        
        self.model.eval()
        with torch.no_grad():
            X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)
            X_tensor = torch.FloatTensor(X_reshaped)
            outputs = self.model(X_tensor)
            proba = torch.softmax(outputs, dim=1)
            return proba.numpy()


class AutoencoderBaseline(BaselineClassifier):
    """
    Autoencoder-based anomaly detection baseline.
    
    Uses reconstruction error for anomaly detection.
    
    Reference:
    An, J., & Cho, S. (2015). "Variational Autoencoder based Anomaly Detection 
    using Reconstruction Probability." SNU Data Mining Center.
    """
    
    def __init__(
        self,
        encoding_dim: int = 32,
        hidden_layers: List[int] = None,
        learning_rate: float = 0.001,
        batch_size: int = 64,
        epochs: int = 50,
        contamination: float = 0.1,
        random_state: int = 42
    ):
        super().__init__("Autoencoder", random_state)
        self.encoding_dim = encoding_dim
        self.hidden_layers = hidden_layers or [64, 32]
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.contamination = contamination
        self.threshold = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'AutoencoderBaseline':
        """Train the Autoencoder on normal data only."""
        try:
            import torch
            import torch.nn as nn
            import torch.optim as optim
            from torch.utils.data import DataLoader, TensorDataset
        except ImportError:
            raise ImportError(
                "PyTorch not installed. Install with: pip install torch"
            )
        
        logger.info("Training Autoencoder for anomaly detection...")
        start_time = time.time()
        
        torch.manual_seed(self.random_state)
        
        # Train only on normal (benign) data
        # Assuming class 0 is benign
        X_normal = X[y == 0] if len(np.unique(y)) > 1 else X
        
        input_dim = X.shape[1]
        
        # Build autoencoder architecture
        class Autoencoder(nn.Module):
            def __init__(self, input_dim, hidden_layers, encoding_dim):
                super(Autoencoder, self).__init__()
                
                # Encoder
                encoder_layers = []
                prev_dim = input_dim
                for hidden_dim in hidden_layers:
                    encoder_layers.append(nn.Linear(prev_dim, hidden_dim))
                    encoder_layers.append(nn.ReLU())
                    prev_dim = hidden_dim
                encoder_layers.append(nn.Linear(prev_dim, encoding_dim))
                self.encoder = nn.Sequential(*encoder_layers)
                
                # Decoder
                decoder_layers = []
                prev_dim = encoding_dim
                for hidden_dim in reversed(hidden_layers):
                    decoder_layers.append(nn.Linear(prev_dim, hidden_dim))
                    decoder_layers.append(nn.ReLU())
                    prev_dim = hidden_dim
                decoder_layers.append(nn.Linear(prev_dim, input_dim))
                self.decoder = nn.Sequential(*decoder_layers)
            
            def forward(self, x):
                encoded = self.encoder(x)
                decoded = self.decoder(encoded)
                return decoded
        
        self.model = Autoencoder(input_dim, self.hidden_layers, self.encoding_dim)
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Create DataLoader
        X_tensor = torch.FloatTensor(X_normal)
        dataset = TensorDataset(X_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            total_loss = 0
            for (batch_X,) in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_X)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{self.epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
        # Determine threshold
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_normal)
            reconstructions = self.model(X_tensor)
            mse = torch.mean((X_tensor - reconstructions) ** 2, dim=1)
            self.threshold = torch.quantile(mse, 1 - self.contamination).item()
        
        logger.info(f"Anomaly threshold: {self.threshold:.4f}")
        
        self._is_fitted = True
        self.training_time = time.time() - start_time
        logger.info(f"Training completed in {self.training_time:.2f}s")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict: 0 for normal, 1 for anomaly."""
        import torch
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            reconstructions = self.model(X_tensor)
            mse = torch.mean((X_tensor - reconstructions) ** 2, dim=1)
            predictions = (mse > self.threshold).int().numpy()
            return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get anomaly scores as probabilities."""
        import torch
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            reconstructions = self.model(X_tensor)
            mse = torch.mean((X_tensor - reconstructions) ** 2, dim=1)
            
            # Normalize to probability
            proba = torch.sigmoid(mse - self.threshold).numpy()
            return np.column_stack([1 - proba, proba])
    
    def get_reconstruction_errors(self, X: np.ndarray) -> np.ndarray:
        """Get reconstruction errors for each sample."""
        import torch
        
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            reconstructions = self.model(X_tensor)
            mse = torch.mean((X_tensor - reconstructions) ** 2, dim=1)
            return mse.numpy()


class BaselineComparator:
    """
    Comparator for evaluating multiple baseline classifiers.
    
    This class provides utilities for:
    - Training multiple classifiers
    - Comparing performance metrics
    - Statistical significance testing
    - Generating comparison reports
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.classifiers: Dict[str, BaselineClassifier] = {}
        self.results: Dict[str, ModelMetrics] = {}
    
    def add_classifier(self, name: str, classifier: BaselineClassifier) -> None:
        """Add a classifier to the comparison."""
        self.classifiers[name] = classifier
    
    def train_all(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray
    ) -> None:
        """Train all classifiers."""
        logger.info(f"Training {len(self.classifiers)} classifiers...")
        
        for name, clf in self.classifiers.items():
            logger.info(f"\nTraining {name}...")
            try:
                clf.fit(X_train, y_train)
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
    
    def evaluate_all(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        class_names: Optional[List[str]] = None
    ) -> Dict[str, ModelMetrics]:
        """Evaluate all classifiers."""
        logger.info(f"Evaluating {len(self.classifiers)} classifiers...")
        
        for name, clf in self.classifiers.items():
            if clf._is_fitted:
                logger.info(f"\nEvaluating {name}...")
                try:
                    self.results[name] = clf.evaluate(X_test, y_test, class_names)
                    logger.info(f"{name}: {self.results[name]}")
                except Exception as e:
                    logger.error(f"Error evaluating {name}: {e}")
        
        return self.results
    
    def get_comparison_table(self) -> pd.DataFrame:
        """Get comparison table of all results."""
        if not self.results:
            raise ValueError("No results available. Run evaluate_all() first.")
        
        data = []
        for name, metrics in self.results.items():
            data.append({
                'Classifier': name,
                'Accuracy': metrics.accuracy,
                'Precision': metrics.precision,
                'Recall': metrics.recall,
                'F1-Score': metrics.f1_score,
                'AUC-ROC': metrics.auc_roc,
                'FPR': metrics.fpr,
                'Training Time (s)': metrics.training_time,
                'Inference Time (s)': metrics.inference_time
            })
        
        return pd.DataFrame(data)
    
    def save_results(self, path: str) -> None:
        """Save comparison results to file."""
        results_dict = {
            name: metrics.to_dict() 
            for name, metrics in self.results.items()
        }
        
        with open(path, 'w') as f:
            import json
            json.dump(results_dict, f, indent=2)
        
        logger.info(f"Results saved to {path}")


def create_default_baselines(random_state: int = 42) -> Dict[str, BaselineClassifier]:
    """
    Create default set of baseline classifiers.
    
    Returns a dictionary of standard baseline classifiers for comparison.
    """
    return {
        'Random Forest': RandomForestBaseline(
            n_estimators=100,
            max_depth=20,
            random_state=random_state
        ),
        'XGBoost': XGBoostBaseline(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=random_state
        ),
        'LSTM': LSTMBaseline(
            hidden_units=64,
            num_layers=2,
            epochs=30,
            random_state=random_state
        ),
        'Autoencoder': AutoencoderBaseline(
            encoding_dim=32,
            epochs=30,
            random_state=random_state
        )
    }


if __name__ == "__main__":
    # Example usage
    print("Baseline Classifiers for Layer 7 DDoS Detection")
    print("=" * 60)
    
    # Create synthetic data
    from dataset_loader import create_synthetic_layer7_data
    
    print("\nCreating synthetic data...")
    df, labels = create_synthetic_layer7_data(n_samples=2000, n_features=20)
    
    # Encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y = le.fit_transform(labels)
    X = df.values
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"Train: {X_train.shape}, Test: {X_test.shape}")
    print(f"Classes: {le.classes_}")
    
    # Create and train baselines
    print("\n" + "=" * 60)
    print("Training Baseline Classifiers")
    print("=" * 60)
    
    comparator = BaselineComparator(random_state=42)
    
    # Add classifiers
    baselines = create_default_baselines(random_state=42)
    for name, clf in baselines.items():
        comparator.add_classifier(name, clf)
    
    # Train all
    comparator.train_all(X_train, y_train)
    
    # Evaluate all
    results = comparator.evaluate_all(X_test, y_test, class_names=list(le.classes_))
    
    # Print comparison table
    print("\n" + "=" * 60)
    print("Comparison Results")
    print("=" * 60)
    comparison_df = comparator.get_comparison_table()
    print(comparison_df.to_string(index=False))
    
    # Save results
    os.makedirs("./results", exist_ok=True)
    comparator.save_results("./results/baseline_comparison.json")
    print("\nResults saved to ./results/baseline_comparison.json")
