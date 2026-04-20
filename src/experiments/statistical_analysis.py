"""
Statistical Analysis Module for Experimental Evaluation
========================================================

This module provides comprehensive statistical analysis tools for
evaluating and comparing DDoS detection methods, including:

- Cross-validation with confidence intervals
- Paired t-tests for method comparison
- ANOVA for multiple method comparison
- Effect size calculations
- Power analysis
- Multiple comparison corrections (Bonferroni, Holm)

References:
- Demšar, J. (2006). "Statistical Comparisons of Classifiers over Multiple Data Sets."
- Kitchenham, B. (2010). "Using Significance Tests in Software Engineering Research."

Author: [Your Name]
Paper: "Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from scipy import stats
from scipy.stats import ttest_rel, f_oneway, wilcoxon, friedmanchisquare
import warnings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CrossValidationResult:
    """Container for cross-validation results."""
    mean_accuracy: float
    std_accuracy: float
    mean_precision: float
    std_precision: float
    mean_recall: float
    std_recall: float
    mean_f1: float
    std_f1: float
    mean_auc: float
    std_auc: float
    
    # Confidence intervals (95%)
    ci_accuracy: Tuple[float, float]
    ci_precision: Tuple[float, float]
    ci_recall: Tuple[float, float]
    ci_f1: Tuple[float, float]
    ci_auc: Tuple[float, float]
    
    # Raw scores per fold
    fold_accuracies: List[float] = field(default_factory=list)
    fold_precisions: List[float] = field(default_factory=list)
    fold_recalls: List[float] = field(default_factory=list)
    fold_f1s: List[float] = field(default_factory=list)
    fold_aucs: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'mean_accuracy': self.mean_accuracy,
            'std_accuracy': self.std_accuracy,
            'mean_precision': self.mean_precision,
            'std_precision': self.std_precision,
            'mean_recall': self.mean_recall,
            'std_recall': self.std_recall,
            'mean_f1': self.mean_f1,
            'std_f1': self.std_f1,
            'mean_auc': self.mean_auc,
            'std_auc': self.std_auc,
            'ci_accuracy': self.ci_accuracy,
            'ci_precision': self.ci_precision,
            'ci_recall': self.ci_recall,
            'ci_f1': self.ci_f1,
            'ci_auc': self.ci_auc
        }
    
    def __str__(self) -> str:
        return (
            f"Accuracy: {self.mean_accuracy:.4f} ± {self.std_accuracy:.4f} "
            f"[{self.ci_accuracy[0]:.4f}, {self.ci_accuracy[1]:.4f}]\n"
            f"Precision: {self.mean_precision:.4f} ± {self.std_precision:.4f}\n"
            f"Recall: {self.mean_recall:.4f} ± {self.std_recall:.4f}\n"
            f"F1-Score: {self.mean_f1:.4f} ± {self.std_f1:.4f}\n"
            f"AUC-ROC: {self.mean_auc:.4f} ± {self.std_auc:.4f}"
        )


@dataclass
class StatisticalTestResult:
    """Container for statistical test results."""
    test_name: str
    statistic: float
    p_value: float
    alpha: float
    significant: bool
    effect_size: Optional[float] = None
    effect_size_type: Optional[str] = None
    interpretation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'test_name': self.test_name,
            'statistic': self.statistic,
            'p_value': self.p_value,
            'alpha': self.alpha,
            'significant': self.significant,
            'effect_size': self.effect_size,
            'effect_size_type': self.effect_size_type,
            'interpretation': self.interpretation
        }


class CrossValidationAnalyzer:
    """
    Analyzer for k-fold cross-validation with statistical rigor.
    
    Provides:
    - Stratified k-fold cross-validation
    - Confidence interval calculation
    - Per-fold metric tracking
    """
    
    def __init__(self, n_splits: int = 10, random_state: int = 42):
        """
        Initialize cross-validation analyzer.
        
        Args:
            n_splits: Number of folds (default: 10)
            random_state: Random seed for reproducibility
        """
        self.n_splits = n_splits
        self.random_state = random_state
    
    def run_cross_validation(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        metrics: List[str] = None
    ) -> CrossValidationResult:
        """
        Run stratified k-fold cross-validation.
        
        Args:
            model: Classifier with fit/predict methods
            X: Feature matrix
            y: Labels
            metrics: List of metrics to compute
        
        Returns:
            CrossValidationResult with all metrics
        """
        from sklearn.model_selection import StratifiedKFold
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, 
            f1_score, roc_auc_score
        )
        
        metrics = metrics or ['accuracy', 'precision', 'recall', 'f1', 'auc']
        
        skf = StratifiedKFold(
            n_splits=self.n_splits,
            shuffle=True,
            random_state=self.random_state
        )
        
        # Store per-fold results
        fold_accuracies = []
        fold_precisions = []
        fold_recalls = []
        fold_f1s = []
        fold_aucs = []
        
        logger.info(f"Running {self.n_splits}-fold cross-validation...")
        
        for fold, (train_idx, test_idx) in enumerate(skf.split(X, y)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Train model
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            fold_accuracies.append(accuracy_score(y_test, y_pred))
            fold_precisions.append(
                precision_score(y_test, y_pred, average='weighted', zero_division=0)
            )
            fold_recalls.append(
                recall_score(y_test, y_pred, average='weighted', zero_division=0)
            )
            fold_f1s.append(
                f1_score(y_test, y_pred, average='weighted', zero_division=0)
            )
            
            # AUC (handle multiclass)
            try:
                if hasattr(model, 'predict_proba'):
                    y_proba = model.predict_proba(X_test)
                    if y_proba.shape[1] == 2:
                        fold_aucs.append(roc_auc_score(y_test, y_proba[:, 1]))
                    else:
                        fold_aucs.append(roc_auc_score(y_test, y_proba, multi_class='ovr'))
                else:
                    fold_aucs.append(0.0)
            except Exception:
                fold_aucs.append(0.0)
            
            logger.info(
                f"Fold {fold+1}: Acc={fold_accuracies[-1]:.4f}, "
                f"F1={fold_f1s[-1]:.4f}"
            )
        
        # Calculate statistics
        def calc_stats(values: List[float]) -> Tuple[float, float, Tuple[float, float]]:
            mean = np.mean(values)
            std = np.std(values, ddof=1)
            # 95% confidence interval
            se = std / np.sqrt(len(values))
            ci = stats.t.interval(
                0.95, 
                len(values) - 1, 
                loc=mean, 
                scale=se
            )
            return mean, std, ci
        
        acc_mean, acc_std, acc_ci = calc_stats(fold_accuracies)
        prec_mean, prec_std, prec_ci = calc_stats(fold_precisions)
        rec_mean, rec_std, rec_ci = calc_stats(fold_recalls)
        f1_mean, f1_std, f1_ci = calc_stats(fold_f1s)
        auc_mean, auc_std, auc_ci = calc_stats(fold_aucs)
        
        return CrossValidationResult(
            mean_accuracy=acc_mean,
            std_accuracy=acc_std,
            mean_precision=prec_mean,
            std_precision=prec_std,
            mean_recall=rec_mean,
            std_recall=rec_std,
            mean_f1=f1_mean,
            std_f1=f1_std,
            mean_auc=auc_mean,
            std_auc=auc_std,
            ci_accuracy=acc_ci,
            ci_precision=prec_ci,
            ci_recall=rec_ci,
            ci_f1=f1_ci,
            ci_auc=auc_ci,
            fold_accuracies=fold_accuracies,
            fold_precisions=fold_precisions,
            fold_recalls=fold_recalls,
            fold_f1s=fold_f1s,
            fold_aucs=fold_aucs
        )


class PairedTestAnalyzer:
    """
    Analyzer for paired statistical tests between two methods.
    
    Supports:
    - Paired t-test
    - Wilcoxon signed-rank test
    - Effect size calculation (Cohen's d)
    """
    
    @staticmethod
    def paired_t_test(
        scores_a: List[float],
        scores_b: List[float],
        alpha: float = 0.05
    ) -> StatisticalTestResult:
        """
        Perform paired t-test between two sets of scores.
        
        Args:
            scores_a: Scores from method A (e.g., cross-validation folds)
            scores_b: Scores from method B
            alpha: Significance level
        
        Returns:
            StatisticalTestResult with test results
        """
        statistic, p_value = ttest_rel(scores_a, scores_b)
        
        # Effect size (Cohen's d)
        diff = np.array(scores_a) - np.array(scores_b)
        cohens_d = np.mean(diff) / np.std(diff, ddof=1) if np.std(diff, ddof=1) > 0 else 0
        
        # Interpretation
        if p_value < alpha:
            if cohens_d > 0:
                interpretation = f"Method A significantly outperforms Method B (d={cohens_d:.3f})"
            else:
                interpretation = f"Method B significantly outperforms Method A (d={abs(cohens_d):.3f})"
        else:
            interpretation = "No significant difference between methods"
        
        return StatisticalTestResult(
            test_name="Paired t-test",
            statistic=statistic,
            p_value=p_value,
            alpha=alpha,
            significant=p_value < alpha,
            effect_size=abs(cohens_d),
            effect_size_type="Cohen's d",
            interpretation=interpretation
        )
    
    @staticmethod
    def wilcoxon_test(
        scores_a: List[float],
        scores_b: List[float],
        alpha: float = 0.05
    ) -> StatisticalTestResult:
        """
        Perform Wilcoxon signed-rank test (non-parametric alternative).
        
        Args:
            scores_a: Scores from method A
            scores_b: Scores from method B
            alpha: Significance level
        
        Returns:
            StatisticalTestResult with test results
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            statistic, p_value = wilcoxon(scores_a, scores_b)
        
        # Effect size (rank-biserial correlation)
        n = len(scores_a)
        effect_size = 1 - (2 * statistic) / (n * (n + 1) / 2) if n > 0 else 0
        
        interpretation = (
            "Significant difference (non-parametric)" if p_value < alpha 
            else "No significant difference"
        )
        
        return StatisticalTestResult(
            test_name="Wilcoxon signed-rank test",
            statistic=statistic,
            p_value=p_value,
            alpha=alpha,
            significant=p_value < alpha,
            effect_size=abs(effect_size),
            effect_size_type="Rank-biserial r",
            interpretation=interpretation
        )


class ANOVAAnalyzer:
    """
    Analyzer for comparing multiple methods using ANOVA.
    
    Supports:
    - One-way ANOVA
    - Friedman test (non-parametric alternative)
    - Post-hoc tests with corrections
    """
    
    @staticmethod
    def one_way_anova(
        method_scores: Dict[str, List[float]],
        alpha: float = 0.05
    ) -> StatisticalTestResult:
        """
        Perform one-way ANOVA across multiple methods.
        
        Args:
            method_scores: Dictionary mapping method names to their scores
            alpha: Significance level
        
        Returns:
            StatisticalTestResult with test results
        """
        scores_list = list(method_scores.values())
        method_names = list(method_scores.keys())
        
        statistic, p_value = f_oneway(*scores_list)
        
        # Effect size (eta-squared)
        all_scores = [s for scores in scores_list for s in scores]
        grand_mean = np.mean(all_scores)
        
        ss_between = sum(
            len(scores) * (np.mean(scores) - grand_mean) ** 2 
            for scores in scores_list
        )
        ss_total = sum(
            (s - grand_mean) ** 2 
            for s in all_scores
        )
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        interpretation = (
            f"Significant difference among methods (η²={eta_squared:.3f})" 
            if p_value < alpha 
            else "No significant difference among methods"
        )
        
        return StatisticalTestResult(
            test_name="One-way ANOVA",
            statistic=statistic,
            p_value=p_value,
            alpha=alpha,
            significant=p_value < alpha,
            effect_size=eta_squared,
            effect_size_type="η² (eta-squared)",
            interpretation=interpretation
        )
    
    @staticmethod
    def friedman_test(
        method_scores: Dict[str, List[float]],
        alpha: float = 0.05
    ) -> StatisticalTestResult:
        """
        Perform Friedman test (non-parametric alternative to ANOVA).
        
        Args:
            method_scores: Dictionary mapping method names to their scores
            alpha: Significance level
        
        Returns:
            StatisticalTestResult with test results
        """
        scores_list = list(method_scores.values())
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            statistic, p_value = friedmanchisquare(*scores_list)
        
        interpretation = (
            "Significant difference among methods (non-parametric)" 
            if p_value < alpha 
            else "No significant difference among methods"
        )
        
        return StatisticalTestResult(
            test_name="Friedman test",
            statistic=statistic,
            p_value=p_value,
            alpha=alpha,
            significant=p_value < alpha,
            interpretation=interpretation
        )
    
    @staticmethod
    def post_hoc_pairwise(
        method_scores: Dict[str, List[float]],
        alpha: float = 0.05,
        correction: str = "bonferroni"
    ) -> pd.DataFrame:
        """
        Perform post-hoc pairwise comparisons with correction.
        
        Args:
            method_scores: Dictionary mapping method names to their scores
            alpha: Significance level
            correction: Correction method ("bonferroni" or "holm")
        
        Returns:
            DataFrame with pairwise comparison results
        """
        method_names = list(method_scores.keys())
        n_methods = len(method_names)
        n_comparisons = n_methods * (n_methods - 1) // 2
        
        # Adjusted alpha
        if correction == "bonferroni":
            adjusted_alpha = alpha / n_comparisons
        else:
            adjusted_alpha = alpha
        
        results = []
        
        for i in range(n_methods):
            for j in range(i + 1, n_methods):
                name_a = method_names[i]
                name_b = method_names[j]
                scores_a = method_scores[name_a]
                scores_b = method_scores[name_b]
                
                # Paired t-test
                statistic, p_value = ttest_rel(scores_a, scores_b)
                
                # Effect size
                diff = np.array(scores_a) - np.array(scores_b)
                cohens_d = np.mean(diff) / np.std(diff, ddof=1) if np.std(diff, ddof=1) > 0 else 0
                
                results.append({
                    'Method A': name_a,
                    'Method B': name_b,
                    't-statistic': statistic,
                    'p-value': p_value,
                    'p-value (adjusted)': min(p_value * n_comparisons, 1.0) if correction == "bonferroni" else p_value,
                    "Cohen's d": cohens_d,
                    'Significant': p_value < adjusted_alpha
                })
        
        return pd.DataFrame(results)


class MultipleComparisonCorrector:
    """
    Utility for correcting p-values in multiple comparisons.
    
    Supports:
    - Bonferroni correction
    - Holm-Bonferroni method
    - Benjamini-Hochberg (FDR)
    """
    
    @staticmethod
    def bonferroni(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, bool]]:
        """
        Apply Bonferroni correction.
        
        Args:
            p_values: List of p-values
            alpha: Significance level
        
        Returns:
            List of (adjusted_p_value, significant) tuples
        """
        n = len(p_values)
        adjusted_alpha = alpha / n
        
        results = []
        for p in p_values:
            adjusted_p = min(p * n, 1.0)
            results.append((adjusted_p, p < adjusted_alpha))
        
        return results
    
    @staticmethod
    def holm_bonferroni(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, bool]]:
        """
        Apply Holm-Bonferroni correction (step-down procedure).
        
        Args:
            p_values: List of p-values
            alpha: Significance level
        
        Returns:
            List of (adjusted_p_value, significant) tuples
        """
        n = len(p_values)
        indexed_p = [(p, i) for i, p in enumerate(p_values)]
        sorted_p = sorted(indexed_p, key=lambda x: x[0])
        
        results = [None] * n
        reject = False
        
        for rank, (p, original_idx) in enumerate(sorted_p):
            adjusted_alpha = alpha / (n - rank)
            adjusted_p = min(p * (n - rank), 1.0)
            
            if not reject and p < adjusted_alpha:
                results[original_idx] = (adjusted_p, True)
            else:
                reject = True
                results[original_idx] = (adjusted_p, False)
        
        return results
    
    @staticmethod
    def benjamini_hochberg(p_values: List[float], q: float = 0.05) -> List[Tuple[float, bool]]:
        """
        Apply Benjamini-Hochberg FDR correction.
        
        Args:
            p_values: List of p-values
            q: False discovery rate
        
        Returns:
            List of (adjusted_p_value, significant) tuples
        """
        n = len(p_values)
        indexed_p = [(p, i) for i, p in enumerate(p_values)]
        sorted_p = sorted(indexed_p, key=lambda x: x[0], reverse=True)
        
        results = [None] * n
        prev_adjusted = 0
        
        for rank, (p, original_idx) in enumerate(sorted_p):
            adjusted_p = min(p * n / (n - rank), 1.0)
            adjusted_p = max(adjusted_p, prev_adjusted)
            prev_adjusted = adjusted_p
            
            results[original_idx] = (adjusted_p, adjusted_p <= q)
        
        return results


def interpret_effect_size(d: float, effect_type: str = "cohens_d") -> str:
    """
    Interpret effect size magnitude.
    
    Args:
        d: Effect size value
        effect_type: Type of effect size
    
    Returns:
        Interpretation string
    """
    d = abs(d)
    
    if effect_type in ["cohens_d", "d"]:
        if d < 0.2:
            return "negligible"
        elif d < 0.5:
            return "small"
        elif d < 0.8:
            return "medium"
        else:
            return "large"
    elif effect_type in ["eta_squared", "η²"]:
        if d < 0.01:
            return "negligible"
        elif d < 0.06:
            return "small"
        elif d < 0.14:
            return "medium"
        else:
            return "large"
    else:
        return "unknown"


def generate_statistical_report(
    cv_results: Dict[str, CrossValidationResult],
    alpha: float = 0.05
) -> str:
    """
    Generate a comprehensive statistical report.
    
    Args:
        cv_results: Cross-validation results for each method
        alpha: Significance level
    
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 70)
    report.append("STATISTICAL ANALYSIS REPORT")
    report.append("=" * 70)
    report.append(f"Significance Level: α = {alpha}")
    report.append(f"Number of Methods: {len(cv_results)}")
    report.append("")
    
    # Summary statistics
    report.append("-" * 70)
    report.append("SUMMARY STATISTICS (Mean ± Std, 95% CI)")
    report.append("-" * 70)
    
    for name, result in cv_results.items():
        report.append(f"\n{name}:")
        report.append(f"  Accuracy:  {result.mean_accuracy:.4f} ± {result.std_accuracy:.4f} "
                      f"[{result.ci_accuracy[0]:.4f}, {result.ci_accuracy[1]:.4f}]")
        report.append(f"  Precision: {result.mean_precision:.4f} ± {result.std_precision:.4f}")
        report.append(f"  Recall:    {result.mean_recall:.4f} ± {result.std_recall:.4f}")
        report.append(f"  F1-Score:  {result.mean_f1:.4f} ± {result.std_f1:.4f}")
        report.append(f"  AUC-ROC:   {result.mean_auc:.4f} ± {result.std_auc:.4f}")
    
    # ANOVA
    if len(cv_results) > 2:
        report.append("\n" + "-" * 70)
        report.append("ANOVA ANALYSIS")
        report.append("-" * 70)
        
        method_scores = {
            name: result.fold_f1s 
            for name, result in cv_results.items()
        }
        
        anova_result = ANOVAAnalyzer.one_way_anova(method_scores, alpha)
        report.append(f"\n{anova_result.test_name}:")
        report.append(f"  F-statistic: {anova_result.statistic:.4f}")
        report.append(f"  p-value: {anova_result.p_value:.4e}")
        report.append(f"  Effect size (η²): {anova_result.effect_size:.4f} "
                      f"({interpret_effect_size(anova_result.effect_size, 'eta_squared')})")
        report.append(f"  Significant: {'Yes' if anova_result.significant else 'No'}")
        
        # Post-hoc
        if anova_result.significant:
            report.append("\n  Post-hoc Pairwise Comparisons (Bonferroni corrected):")
            post_hoc = ANOVAAnalyzer.post_hoc_pairwise(method_scores, alpha, "bonferroni")
            report.append(post_hoc.to_string(index=False))
    
    # Pairwise comparisons
    if len(cv_results) == 2:
        report.append("\n" + "-" * 70)
        report.append("PAIRWISE COMPARISON")
        report.append("-" * 70)
        
        names = list(cv_results.keys())
        scores_a = cv_results[names[0]].fold_f1s
        scores_b = cv_results[names[1]].fold_f1s
        
        t_test = PairedTestAnalyzer.paired_t_test(scores_a, scores_b, alpha)
        report.append(f"\n{t_test.test_name}:")
        report.append(f"  t-statistic: {t_test.statistic:.4f}")
        report.append(f"  p-value: {t_test.p_value:.4e}")
        report.append(f"  Effect size (Cohen's d): {t_test.effect_size:.4f} "
                      f"({interpret_effect_size(t_test.effect_size, 'cohens_d')})")
        report.append(f"  Significant: {'Yes' if t_test.significant else 'No'}")
        report.append(f"  Interpretation: {t_test.interpretation}")
    
    report.append("\n" + "=" * 70)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    print("Statistical Analysis Module")
    print("=" * 60)
    
    # Simulate cross-validation results
    np.random.seed(42)
    n_folds = 10
    
    # Simulated results for 3 methods
    methods = {
        'Knowledge Graph': {
            'f1': [0.93 + np.random.normal(0, 0.02) for _ in range(n_folds)],
            'acc': [0.94 + np.random.normal(0, 0.02) for _ in range(n_folds)]
        },
        'Random Forest': {
            'f1': [0.90 + np.random.normal(0, 0.03) for _ in range(n_folds)],
            'acc': [0.91 + np.random.normal(0, 0.03) for _ in range(n_folds)]
        },
        'XGBoost': {
            'f1': [0.91 + np.random.normal(0, 0.025) for _ in range(n_folds)],
            'acc': [0.92 + np.random.normal(0, 0.025) for _ in range(n_folds)]
        }
    }
    
    # Create mock CV results
    cv_results = {}
    for name, scores in methods.items():
        f1s = scores['f1']
        accs = scores['acc']
        
        cv_results[name] = CrossValidationResult(
            mean_accuracy=np.mean(accs),
            std_accuracy=np.std(accs, ddof=1),
            mean_precision=np.mean(f1s) * 0.98,
            std_precision=np.std(f1s, ddof=1) * 0.9,
            mean_recall=np.mean(f1s) * 0.97,
            std_recall=np.std(f1s, ddof=1) * 0.95,
            mean_f1=np.mean(f1s),
            std_f1=np.std(f1s, ddof=1),
            mean_auc=np.mean(f1s) * 1.02,
            std_auc=np.std(f1s, ddof=1) * 1.1,
            ci_accuracy=(np.mean(accs) - 0.02, np.mean(accs) + 0.02),
            ci_precision=(np.mean(f1s) - 0.02, np.mean(f1s) + 0.02),
            ci_recall=(np.mean(f1s) - 0.02, np.mean(f1s) + 0.02),
            ci_f1=(np.mean(f1s) - 0.02, np.mean(f1s) + 0.02),
            ci_auc=(np.mean(f1s) - 0.02, np.mean(f1s) + 0.02),
            fold_f1s=f1s,
            fold_accuracies=accs
        )
    
    # Generate report
    report = generate_statistical_report(cv_results)
    print(report)
    
    # Test pairwise comparison
    print("\n" + "=" * 60)
    print("PAIRWISE T-TEST EXAMPLE")
    print("=" * 60)
    
    t_test = PairedTestAnalyzer.paired_t_test(
        methods['Knowledge Graph']['f1'],
        methods['Random Forest']['f1']
    )
    print(f"\nKnowledge Graph vs Random Forest:")
    print(f"  t-statistic: {t_test.statistic:.4f}")
    print(f"  p-value: {t_test.p_value:.4e}")
    print(f"  Significant: {t_test.significant}")
    print(f"  Effect size: {t_test.effect_size:.4f} ({interpret_effect_size(t_test.effect_size)})")
    print(f"  {t_test.interpretation}")
