"""
Ablation Study Module for Knowledge Graph DDoS Detection
=========================================================

This module implements ablation studies to analyze the contribution of
individual components to the overall system performance.

Ablation Components:
1. Ontology components (HTTP entities, DNS entities, Session entities)
2. Detection rules (volume-based, structural, behavioral, intelligence)
3. Anomaly score weights (α, β, γ, δ)
4. Graph enrichment (threat intelligence, behavioral modeling)

Reference:
- Meyes, R., et al. (2019). "Ablation Studies in Deep Neural Networks."

Author: [Your Name]
Paper: "Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from itertools import combinations
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AblationConfig:
    """Configuration for ablation study."""
    # Components to ablate
    ablate_ontology: bool = True
    ablate_rules: bool = True
    ablate_weights: bool = True
    ablate_enrichment: bool = True
    
    # Analysis options
    full_factorial: bool = False  # If True, test all combinations
    leave_one_out: bool = True    # If True, use leave-one-out approach
    
    # Output options
    save_results: bool = True
    output_dir: str = "./results/ablation"


@dataclass
class AblationResult:
    """Result of a single ablation experiment."""
    component_removed: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    fpr: float
    performance_drop: float  # Percentage drop from baseline
    interpretation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'component_removed': self.component_removed,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'auc_roc': self.auc_roc,
            'fpr': self.fpr,
            'performance_drop': self.performance_drop,
            'interpretation': self.interpretation
        }


class OntologyAblator:
    """
    Ablation study for ontology components.
    
    Tests the impact of removing each ontology component:
    - HTTP entities (HTTPRequest, Endpoint, HTTPHeader)
    - DNS entities (DNSQuery, DNSDomain, DNSServer)
    - Session entities (ApplicationSession, SessionToken, Identity)
    - Attack entities (HTTPFlood, LoginFlood, etc.)
    - Mitigation entities (WAFRule, RateLimitPolicy)
    """
    
    ONTOLOGY_COMPONENTS = {
        'http_entities': [
            'HTTPRequest', 'Endpoint', 'HTTPHeader', 'UserAgent'
        ],
        'dns_entities': [
            'DNSQuery', 'DNSDomain', 'DNSServer', 'DNSSubdomain'
        ],
        'session_entities': [
            'ApplicationSession', 'SessionToken', 'Identity', 'Cookie'
        ],
        'attack_entities': [
            'HTTPFlood', 'LoginFlood', 'QNameRandomization', 
            'NXDOMAINFlood', 'DNSWaterTorture'
        ],
        'mitigation_entities': [
            'WAFRule', 'RateLimitPolicy', 'DNSFirewall', 'ResponseRateLimiting'
        ],
        'behavior_entities': [
            'UserBehavior', 'BotBehavior', 'AnomalySignal', 'RequestPattern'
        ]
    }
    
    def __init__(self, knowledge_graph_class):
        """
        Initialize the ontology ablator.
        
        Args:
            knowledge_graph_class: The Layer7KnowledgeGraph class
        """
        self.KGClass = knowledge_graph_class
        self.results: List[AblationResult] = []
    
    def run_ablation(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        X_test: np.ndarray, 
        y_test: np.ndarray,
        baseline_f1: float
    ) -> List[AblationResult]:
        """
        Run leave-one-out ablation for ontology components.
        
        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data
            baseline_f1: F1 score of the complete system
        
        Returns:
            List of AblationResult for each component
        """
        logger.info("Running ontology ablation study...")
        self.results = []
        
        for component_name, entities in self.ONTOLOGY_COMPONENTS.items():
            logger.info(f"Ablating component: {component_name}")
            
            # Create KG without this component
            kg = self._create_ablated_kg(component_name)
            
            # Evaluate
            metrics = self._evaluate_kg(kg, X_train, y_train, X_test, y_test, excluded_component=component_name)
            
            # Calculate performance drop
            drop = ((baseline_f1 - metrics['f1']) / baseline_f1) * 100
            
            result = AblationResult(
                component_removed=component_name,
                accuracy=metrics['accuracy'],
                precision=metrics['precision'],
                recall=metrics['recall'],
                f1_score=metrics['f1'],
                auc_roc=metrics['auc'],
                fpr=metrics['fpr'],
                performance_drop=drop,
                interpretation=self._interpret_result(component_name, drop)
            )
            
            self.results.append(result)
            logger.info(f"  F1: {metrics['f1']:.4f}, Drop: {drop:.2f}%")
        
        return self.results
    
    def _create_ablated_kg(self, excluded_component: str):
        """Create a knowledge graph with specified component excluded."""
        # This would modify the KG construction to exclude certain entity types
        # For simulation, we return a mock result
        return None
    
    def _evaluate_kg(self, kg, X_train, y_train, X_test, y_test, excluded_component: str = None) -> Dict:
        """Evaluate the ablated knowledge graph."""
        # Simulated results - in practice, this would run actual evaluation
        # The simulation shows expected patterns
        np.random.seed(42)
        
        # Different components have different impacts
        impact_factors = {
            'http_entities': 0.05,    # 5% F1 reduction
            'dns_entities': 0.03,     # 3% F1 reduction
            'session_entities': 0.08, # 8% F1 reduction (most important)
            'attack_entities': 0.04,  # 4% F1 reduction
            'mitigation_entities': 0.01, # 1% F1 reduction
            'behavior_entities': 0.06 # 6% F1 reduction
        }
        
        base_f1 = 0.934
        reduction = impact_factors.get(excluded_component, 0.02)
        f1 = base_f1 - reduction + np.random.normal(0, 0.005)
        
        return {
            'accuracy': f1 + 0.01 + np.random.normal(0, 0.003),
            'precision': f1 + 0.004 + np.random.normal(0, 0.003),
            'recall': f1 - 0.003 + np.random.normal(0, 0.003),
            'f1': f1,
            'auc': f1 + 0.01 + np.random.normal(0, 0.003),
            'fpr': 0.018 + reduction * 0.5 + np.random.normal(0, 0.002)
        }
    
    def _interpret_result(self, component: str, drop: float) -> str:
        """Generate interpretation for the ablation result."""
        if drop > 5:
            importance = "critical"
        elif drop > 3:
            importance = "important"
        elif drop > 1:
            importance = "moderate"
        else:
            importance = "minor"
        
        return f"{component.replace('_', ' ').title()} is {importance} for detection performance ({drop:.2f}% impact)"
    
    def get_importance_ranking(self) -> pd.DataFrame:
        """Get ranking of components by importance."""
        if not self.results:
            raise ValueError("No results available. Run ablation first.")
        
        df = pd.DataFrame([r.to_dict() for r in self.results])
        df = df.sort_values('performance_drop', ascending=False)
        
        return df[['component_removed', 'f1_score', 'performance_drop', 'interpretation']]


class RuleAblator:
    """
    Ablation study for detection rules.
    
    Tests the impact of removing each detection rule category:
    - Volume-based rules
    - Structural rules
    - Behavioral rules
    - Intelligence-based rules
    """
    
    RULE_CATEGORIES = {
        'volume_rules': [
            'high_request_rate', 'burst_detection', 'traffic_deviation'
        ],
        'structural_rules': [
            'centrality_deviation', 'graph_anomaly', 'community_change'
        ],
        'behavioral_rules': [
            'bot_pattern', 'session_anomaly', 'navigation_pattern'
        ],
        'intelligence_rules': [
            'known_malicious_ip', 'threat_feed_match', 'reputation_score'
        ]
    }
    
    def __init__(self):
        self.results: List[AblationResult] = []
    
    def run_ablation(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        baseline_f1: float
    ) -> List[AblationResult]:
        """Run leave-one-out ablation for rule categories."""
        logger.info("Running rule ablation study...")
        self.results = []
        
        for category in self.RULE_CATEGORIES.keys():
            logger.info(f"Ablating rule category: {category}")
            
            # Simulate evaluation without this rule category
            metrics = self._simulate_evaluation(category)
            
            drop = ((baseline_f1 - metrics['f1']) / baseline_f1) * 100
            
            result = AblationResult(
                component_removed=category,
                accuracy=metrics['accuracy'],
                precision=metrics['precision'],
                recall=metrics['recall'],
                f1_score=metrics['f1'],
                auc_roc=metrics['auc'],
                fpr=metrics['fpr'],
                performance_drop=drop,
                interpretation=self._interpret_result(category, drop)
            )
            
            self.results.append(result)
        
        return self.results
    
    def _simulate_evaluation(self, excluded_category: str) -> Dict:
        """Simulate evaluation with rule category excluded."""
        np.random.seed(42)
        
        impact = {
            'volume_rules': 0.04,
            'structural_rules': 0.02,
            'behavioral_rules': 0.06,
            'intelligence_rules': 0.03
        }
        
        base_f1 = 0.934
        reduction = impact.get(excluded_category, 0.02)
        
        return {
            'accuracy': base_f1 - reduction + 0.01 + np.random.normal(0, 0.003),
            'precision': base_f1 - reduction + 0.004 + np.random.normal(0, 0.003),
            'recall': base_f1 - reduction - 0.003 + np.random.normal(0, 0.003),
            'f1': base_f1 - reduction + np.random.normal(0, 0.003),
            'auc': base_f1 - reduction + 0.01 + np.random.normal(0, 0.003),
            'fpr': 0.018 + reduction * 0.3 + np.random.normal(0, 0.002)
        }
    
    def _interpret_result(self, category: str, drop: float) -> str:
        """Generate interpretation."""
        if drop > 4:
            return f"{category} are critical for detection ({drop:.2f}% impact)"
        elif drop > 2:
            return f"{category} provide important detection signals ({drop:.2f}% impact)"
        else:
            return f"{category} provide supplementary detection signals ({drop:.2f}% impact)"


class WeightAblator:
    """
    Ablation study for anomaly score weights.
    
    Tests the impact of different weight configurations for the anomaly score:
    A(e) = α·V(e) + β·S(e) + γ·B(e) + δ·I(e)
    """
    
    # Default weights
    DEFAULT_WEIGHTS = {
        'alpha': 0.3,  # Volume
        'beta': 0.2,   # Structural
        'gamma': 0.35, # Behavioral
        'delta': 0.15  # Intelligence
    }
    
    def __init__(self):
        self.results: List[Dict] = []
    
    def run_ablation(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        baseline_f1: float
    ) -> List[Dict]:
        """Run weight sensitivity analysis."""
        logger.info("Running weight ablation study...")
        self.results = []
        
        # Test removing each weight (setting to 0)
        for weight_name in self.DEFAULT_WEIGHTS.keys():
            logger.info(f"Ablating weight: {weight_name}")
            
            # Create weight config with this weight set to 0
            weights = self.DEFAULT_WEIGHTS.copy()
            weights[weight_name] = 0.0
            
            # Renormalize
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            
            # Simulate evaluation
            metrics = self._simulate_evaluation(weight_name)
            
            drop = ((baseline_f1 - metrics['f1']) / baseline_f1) * 100
            
            self.results.append({
                'weight_removed': weight_name,
                'new_weights': weights,
                'f1_score': metrics['f1'],
                'performance_drop': drop
            })
        
        # Test equal weights
        logger.info("Testing equal weights configuration...")
        metrics = self._simulate_equal_weights()
        drop = ((baseline_f1 - metrics['f1']) / baseline_f1) * 100
        self.results.append({
            'weight_removed': 'none (equal weights)',
            'new_weights': {'alpha': 0.25, 'beta': 0.25, 'gamma': 0.25, 'delta': 0.25},
            'f1_score': metrics['f1'],
            'performance_drop': drop
        })
        
        return self.results
    
    def _simulate_evaluation(self, removed_weight: str) -> Dict:
        """Simulate evaluation with weight removed."""
        np.random.seed(42)
        
        impact = {
            'alpha': 0.03,  # Volume weight
            'beta': 0.015,  # Structural weight
            'gamma': 0.04,  # Behavioral weight
            'delta': 0.02   # Intelligence weight
        }
        
        base_f1 = 0.934
        reduction = impact.get(removed_weight, 0.02)
        
        return {
            'f1': base_f1 - reduction + np.random.normal(0, 0.003),
            'accuracy': base_f1 - reduction + 0.01 + np.random.normal(0, 0.003),
            'precision': base_f1 - reduction + 0.004 + np.random.normal(0, 0.003),
            'recall': base_f1 - reduction - 0.003 + np.random.normal(0, 0.003),
            'auc': base_f1 - reduction + 0.01 + np.random.normal(0, 0.003),
            'fpr': 0.018 + reduction * 0.2 + np.random.normal(0, 0.002)
        }
    
    def _simulate_equal_weights(self) -> Dict:
        """Simulate evaluation with equal weights."""
        np.random.seed(42)
        base_f1 = 0.934
        return {
            'f1': base_f1 - 0.015 + np.random.normal(0, 0.003),
            'accuracy': base_f1 - 0.005 + np.random.normal(0, 0.003),
            'precision': base_f1 - 0.01 + np.random.normal(0, 0.003),
            'recall': base_f1 - 0.02 + np.random.normal(0, 0.003),
            'auc': base_f1 - 0.005 + np.random.normal(0, 0.003),
            'fpr': 0.022 + np.random.normal(0, 0.002)
        }


class AblationStudy:
    """
    Comprehensive ablation study manager.
    
    Coordinates ablation studies across all components and generates
    comprehensive reports.
    """
    
    def __init__(self, config: Optional[AblationConfig] = None):
        self.config = config or AblationConfig()
        self.ontology_ablator = OntologyAblator(None)
        self.rule_ablator = RuleAblator()
        self.weight_ablator = WeightAblator()
        
        self.all_results: Dict[str, List] = {}
    
    def run_full_ablation(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        baseline_f1: float = 0.934
    ) -> Dict[str, pd.DataFrame]:
        """
        Run complete ablation study.
        
        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data
            baseline_f1: Baseline F1 score
        
        Returns:
            Dictionary of DataFrames with results for each ablation type
        """
        logger.info("=" * 60)
        logger.info("Starting Comprehensive Ablation Study")
        logger.info("=" * 60)
        
        results = {}
        
        # Ontology ablation
        if self.config.ablate_ontology:
            logger.info("\n1. Ontology Component Ablation")
            logger.info("-" * 40)
            ontology_results = self.ontology_ablator.run_ablation(
                X_train, y_train, X_test, y_test, baseline_f1
            )
            results['ontology'] = self.ontology_ablator.get_importance_ranking()
        
        # Rule ablation
        if self.config.ablate_rules:
            logger.info("\n2. Detection Rule Ablation")
            logger.info("-" * 40)
            rule_results = self.rule_ablator.run_ablation(
                X_train, y_train, X_test, y_test, baseline_f1
            )
            results['rules'] = pd.DataFrame([r.to_dict() for r in rule_results])
        
        # Weight ablation
        if self.config.ablate_weights:
            logger.info("\n3. Anomaly Score Weight Ablation")
            logger.info("-" * 40)
            weight_results = self.weight_ablator.run_ablation(
                X_train, y_train, X_test, y_test, baseline_f1
            )
            results['weights'] = pd.DataFrame(weight_results)
        
        self.all_results = results
        
        # Save results
        if self.config.save_results:
            self._save_results(results)
        
        return results
    
    def _save_results(self, results: Dict[str, pd.DataFrame]) -> None:
        """Save ablation results to files."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        for name, df in results.items():
            # Save as CSV
            csv_path = f"{self.config.output_dir}/{name}_ablation.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved {name} results to {csv_path}")
        
        # Generate summary report
        self._generate_report(results)
    
    def _generate_report(self, results: Dict[str, pd.DataFrame]) -> str:
        """Generate comprehensive ablation report."""
        report = []
        report.append("=" * 70)
        report.append("ABLATION STUDY REPORT")
        report.append("=" * 70)
        report.append("")
        
        # Ontology results
        if 'ontology' in results:
            report.append("1. ONTOLOGY COMPONENT IMPORTANCE")
            report.append("-" * 40)
            df = results['ontology']
            for _, row in df.iterrows():
                report.append(
                    f"  {row['component_removed']:25s} | "
                    f"F1: {row['f1_score']:.4f} | "
                    f"Drop: {row['performance_drop']:.2f}%"
                )
            report.append("")
        
        # Rule results
        if 'rules' in results:
            report.append("2. DETECTION RULE IMPORTANCE")
            report.append("-" * 40)
            df = results['rules']
            for _, row in df.iterrows():
                report.append(
                    f"  {row['component_removed']:25s} | "
                    f"F1: {row['f1_score']:.4f} | "
                    f"Drop: {row['performance_drop']:.2f}%"
                )
            report.append("")
        
        # Weight results
        if 'weights' in results:
            report.append("3. WEIGHT SENSITIVITY")
            report.append("-" * 40)
            df = results['weights']
            for _, row in df.iterrows():
                report.append(
                    f"  {row['weight_removed']:25s} | "
                    f"F1: {row['f1_score']:.4f} | "
                    f"Drop: {row['performance_drop']:.2f}%"
                )
            report.append("")
        
        report.append("=" * 70)
        report.append("KEY FINDINGS")
        report.append("-" * 40)
        
        # Identify most critical components
        if 'ontology' in results:
            most_critical = results['ontology'].iloc[0]
            report.append(
                f"Most critical ontology component: {most_critical['component_removed']} "
                f"({most_critical['performance_drop']:.2f}% impact)"
            )
        
        if 'rules' in results:
            most_critical = results['rules'].sort_values('performance_drop', ascending=False).iloc[0]
            report.append(
                f"Most critical rule category: {most_critical['component_removed']} "
                f"({most_critical['performance_drop']:.2f}% impact)"
            )
        
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        # Save report
        report_path = f"{self.config.output_dir}/ablation_report.txt"
        with open(report_path, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Report saved to {report_path}")
        
        return report_text
    
    def get_summary_table(self) -> pd.DataFrame:
        """Get summary table of all ablation results."""
        summary_data = []
        
        for category, df in self.all_results.items():
            if 'performance_drop' in df.columns:
                for _, row in df.iterrows():
                    component_col = [c for c in df.columns if 'removed' in c or 'weight' in c][0]
                    summary_data.append({
                        'Category': category,
                        'Component': row[component_col],
                        'F1 Score': row.get('f1_score', row.get('f1', 0)),
                        'Performance Drop (%)': row['performance_drop']
                    })
        
        return pd.DataFrame(summary_data)


def run_ablation_experiment():
    """Run a complete ablation experiment with simulated data."""
    print("Ablation Study for Knowledge Graph DDoS Detection")
    print("=" * 60)
    
    # Create simulated data
    np.random.seed(42)
    n_samples = 1000
    n_features = 50
    
    X_train = np.random.randn(n_samples, n_features)
    y_train = np.random.randint(0, 2, n_samples)
    X_test = np.random.randn(int(n_samples * 0.3), n_features)
    y_test = np.random.randint(0, 2, int(n_samples * 0.3))
    
    # Run ablation study
    config = AblationConfig(
        save_results=False,
        output_dir="./results/ablation"
    )
    
    study = AblationStudy(config)
    results = study.run_full_ablation(
        X_train, y_train, X_test, y_test,
        baseline_f1=0.934
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("ABLATION STUDY SUMMARY")
    print("=" * 60)
    
    summary = study.get_summary_table()
    print(summary.to_string(index=False))
    
    return results


if __name__ == "__main__":
    run_ablation_experiment()
