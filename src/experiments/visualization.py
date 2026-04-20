"""
Experimental Results Visualization Module
==========================================

This module provides comprehensive visualization capabilities for experimental
results from the Knowledge Graph-based DDoS detection system.

Visualization Types:
1. Ablation study visualizations (bar charts, heatmaps, importance rankings)
2. Baseline classifier comparisons (performance tables, ROC curves)
3. Statistical analysis plots (significance tests, confidence intervals)
4. Publication-ready figures (LaTeX-compatible output)

Dependencies:
- matplotlib: Core plotting library
- seaborn: Statistical visualizations
- numpy, pandas: Data manipulation
- plotly (optional): Interactive visualizations

Author: [Your Name]
Paper: "Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks"
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging
import json

# Visualization imports
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns

# Configure matplotlib for publication quality
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.3
})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for visualization settings."""
    # Figure settings
    figsize: Tuple[int, int] = (10, 6)
    dpi: int = 300
    style: str = 'seaborn-v0_8-whitegrid'
    
    # Color settings
    color_palette: str = 'colorblind'  # seaborn colorblind-friendly palette
    primary_color: str = '#2E86AB'
    secondary_color: str = '#A23B72'
    accent_colors: List[str] = field(default_factory=lambda: [
        '#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B',
        '#95C623', '#4A6FA5', '#7D4E57', '#8B9A46', '#6B7FD7'
    ])
    
    # Output settings
    output_dir: str = './results/figures'
    save_format: str = 'pdf'  # pdf, png, svg, eps
    save_latex: bool = True  # Also save LaTeX table
    
    # Plot-specific settings
    bar_width: float = 0.35
    error_bar_capsize: float = 3.0
    line_width: float = 2.0
    marker_size: float = 8.0
    
    # Statistical display
    show_confidence_intervals: bool = True
    show_significance: bool = True
    significance_level: float = 0.05
    confidence_level: float = 0.95


class AblationVisualizer:
    """
    Visualization tools for ablation study results.
    
    Creates publication-ready visualizations for:
    - Component importance bar charts
    - Performance drop heatmaps
    - Comparative analysis plots
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self._setup_style()
    
    def _setup_style(self):
        """Set up matplotlib style."""
        try:
            plt.style.use(self.config.style)
        except:
            plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette(self.config.color_palette)
    
    def plot_component_importance(
        self,
        results: pd.DataFrame,
        component_col: str = 'component_removed',
        metric_col: str = 'performance_drop',
        title: str = "Component Importance Analysis",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Create horizontal bar chart showing component importance.
        
        Args:
            results: DataFrame with ablation results
            component_col: Column name for component names
            metric_col: Column name for performance metric
            title: Plot title
            save_path: Path to save figure (optional)
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)
        
        # Auto-detect component column if not found
        if component_col not in results.columns:
            possible_cols = [c for c in results.columns if 'removed' in c.lower() or 'component' in c.lower() or 'weight' in c.lower()]
            if possible_cols:
                component_col = possible_cols[0]
        
        # Sort by importance
        df_sorted = results.sort_values(metric_col, ascending=True)
        
        # Create color gradient based on importance
        colors = self._get_importance_colors(df_sorted[metric_col].values)
        
        # Create horizontal bar chart
        bars = ax.barh(
            range(len(df_sorted)),
            df_sorted[metric_col],
            color=colors,
            edgecolor='black',
            linewidth=0.5,
            height=0.7
        )
        
        # Customize
        ax.set_yticks(range(len(df_sorted)))
        ax.set_yticklabels(df_sorted[component_col], fontsize=10)
        ax.set_xlabel('Performance Drop (%)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, df_sorted[metric_col])):
            ax.text(
                val + 0.1, i,
                f'{val:.2f}%',
                va='center',
                fontsize=9
            )
        
        # Add importance threshold lines
        ax.axvline(x=5, color='red', linestyle='--', alpha=0.5, label='Critical threshold')
        ax.axvline(x=3, color='orange', linestyle='--', alpha=0.5, label='Important threshold')
        
        ax.legend(loc='lower right', fontsize=8)
        ax.set_xlim(0, max(df_sorted[metric_col]) * 1.2)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_ablation_comparison(
        self,
        results_dict: Dict[str, pd.DataFrame],
        metric: str = 'f1_score',
        baseline_value: float = 0.934,
        title: str = "Ablation Study Comparison",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Create grouped bar chart comparing ablation results across categories.
        
        Args:
            results_dict: Dictionary of DataFrames for each ablation category
            metric: Metric to compare
            baseline_value: Baseline performance value
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Prepare data
        categories = list(results_dict.keys())
        n_categories = len(categories)
        
        # Get max number of components in any category
        max_components = max(len(df) for df in results_dict.values())
        
        # Create grouped bars
        x = np.arange(max_components)
        width = self.config.bar_width / n_categories
        
        for i, (category, df) in enumerate(results_dict.items()):
            # Get component names and values
            component_col = [c for c in df.columns if 'removed' in c or 'component' in c.lower()][0]
            values = df[metric].values if metric in df.columns else df['f1_score'].values
            
            # Pad if necessary
            if len(values) < max_components:
                values = np.pad(values, (0, max_components - len(values)), 
                               constant_values=np.nan)
            
            offset = (i - n_categories/2 + 0.5) * width
            bars = ax.bar(
                x + offset, values, width,
                label=category.title(),
                color=self.config.accent_colors[i % len(self.config.accent_colors)],
                edgecolor='black',
                linewidth=0.5
            )
            
            # Add value labels
            for bar, val in zip(bars, values):
                if not np.isnan(val):
                    ax.text(
                        bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.005,
                        f'{val:.3f}',
                        ha='center', va='bottom',
                        fontsize=7, rotation=45
                    )
        
        # Add baseline line
        ax.axhline(y=baseline_value, color='red', linestyle='--', 
                  linewidth=2, label=f'Baseline ({baseline_value:.3f})')
        
        ax.set_xlabel('Component Index', fontsize=11)
        ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.set_ylim(0.85, baseline_value + 0.02)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_importance_heatmap(
        self,
        results_dict: Dict[str, pd.DataFrame],
        metric: str = 'performance_drop',
        title: str = "Component Importance Heatmap",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Create heatmap showing importance across all ablation categories.
        
        Args:
            results_dict: Dictionary of DataFrames for each ablation category
            metric: Metric to visualize
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        # Prepare data for heatmap
        all_components = []
        all_values = []
        row_labels = []
        
        for category, df in results_dict.items():
            component_col = [c for c in df.columns if 'removed' in c or 'component' in c.lower()][0]
            for _, row in df.iterrows():
                all_components.append(row[component_col])
                all_values.append(row.get(metric, row.get('performance_drop', 0)))
                row_labels.append(category)
        
        # Create pivot table
        heatmap_df = pd.DataFrame({
            'Category': row_labels,
            'Component': all_components,
            'Value': all_values
        })
        
        # Reshape for heatmap (components as columns, categories as rows)
        pivot_df = heatmap_df.pivot_table(
            values='Value',
            index='Category',
            columns='Component',
            aggfunc='first'
        )
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(14, 6))
        
        sns.heatmap(
            pivot_df,
            annot=True,
            fmt='.2f',
            cmap='RdYlGn_r',  # Red for high importance, green for low
            center=3,  # Center colormap at moderate importance
            linewidths=0.5,
            ax=ax,
            cbar_kws={'label': 'Performance Drop (%)'}
        )
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Component', fontsize=11)
        ax.set_ylabel('Category', fontsize=11)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def _get_importance_colors(self, values: np.ndarray) -> List[str]:
        """Generate colors based on importance values."""
        colors = []
        for val in values:
            if val > 5:
                colors.append('#C73E1D')  # Red - critical
            elif val > 3:
                colors.append('#F18F01')  # Orange - important
            elif val > 1:
                colors.append('#95C623')  # Yellow-green - moderate
            else:
                colors.append('#2E86AB')  # Blue - minor
        return colors
    
    def _save_figure(self, fig: Figure, path: str):
        """Save figure in specified format."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        full_path = f"{self.config.output_dir}/{path}"
        
        # Save in primary format
        fig.savefig(f"{full_path}.{self.config.save_format}", 
                   dpi=self.config.dpi, bbox_inches='tight')
        
        # Also save as PNG for preview
        fig.savefig(f"{full_path}.png", dpi=self.config.dpi, bbox_inches='tight')
        
        logger.info(f"Figure saved to {full_path}.{self.config.save_format}")


class BaselineComparisonVisualizer:
    """
    Visualization tools for baseline classifier comparisons.
    
    Creates:
    - Performance comparison tables
    - ROC curves
    - Precision-Recall curves
    - Radar charts for multi-metric comparison
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self._setup_style()
    
    def _setup_style(self):
        """Set up matplotlib style."""
        try:
            plt.style.use(self.config.style)
        except:
            plt.style.use('seaborn-v0_8-whitegrid')
    
    def plot_performance_comparison(
        self,
        results: Dict[str, Dict[str, float]],
        metrics: List[str] = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc'],
        title: str = "Classifier Performance Comparison",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Create grouped bar chart comparing classifier performance.
        
        Args:
            results: Dictionary mapping classifier names to metric dictionaries
            metrics: List of metrics to compare
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        classifiers = list(results.keys())
        n_classifiers = len(classifiers)
        n_metrics = len(metrics)
        
        x = np.arange(n_metrics)
        width = self.config.bar_width / n_classifiers
        
        for i, (clf_name, clf_metrics) in enumerate(results.items()):
            values = [clf_metrics.get(m, 0) for m in metrics]
            offset = (i - n_classifiers/2 + 0.5) * width
            
            bars = ax.bar(
                x + offset, values, width,
                label=clf_name,
                color=self.config.accent_colors[i % len(self.config.accent_colors)],
                edgecolor='black',
                linewidth=0.5
            )
            
            # Add value labels
            for bar, val in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.01,
                    f'{val:.3f}',
                    ha='center', va='bottom',
                    fontsize=7, rotation=45
                )
        
        ax.set_xlabel('Metric', fontsize=11)
        ax.set_ylabel('Score', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics], fontsize=10)
        ax.legend(loc='upper right', fontsize=9)
        ax.set_ylim(0, 1.15)
        
        # Add grid
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_roc_curves(
        self,
        roc_data: Dict[str, Tuple[np.ndarray, np.ndarray, float]],
        title: str = "ROC Curve Comparison",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Plot ROC curves for multiple classifiers.
        
        Args:
            roc_data: Dictionary mapping classifier names to (fpr, tpr, auc) tuples
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        
        for i, (clf_name, (fpr, tpr, auc)) in enumerate(roc_data.items()):
            ax.plot(
                fpr, tpr,
                color=self.config.accent_colors[i % len(self.config.accent_colors)],
                linewidth=self.config.line_width,
                label=f'{clf_name} (AUC = {auc:.3f})'
            )
        
        # Add diagonal reference line
        ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        
        ax.set_xlabel('False Positive Rate', fontsize=11)
        ax.set_ylabel('True Positive Rate', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(loc='lower right', fontsize=9)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        ax.grid(True, alpha=0.3)
        
        # Add shaded region for best classifier
        best_clf = max(roc_data.items(), key=lambda x: x[1][2])
        ax.fill_between(
            best_clf[1][0], best_clf[1][1], 0,
            alpha=0.1,
            color=self.config.primary_color
        )
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_precision_recall_curves(
        self,
        pr_data: Dict[str, Tuple[np.ndarray, np.ndarray, float]],
        title: str = "Precision-Recall Curve Comparison",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Plot Precision-Recall curves for multiple classifiers.
        
        Args:
            pr_data: Dictionary mapping classifier names to (precision, recall, ap) tuples
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        
        for i, (clf_name, (precision, recall, ap)) in enumerate(pr_data.items()):
            ax.plot(
                recall, precision,
                color=self.config.accent_colors[i % len(self.config.accent_colors)],
                linewidth=self.config.line_width,
                label=f'{clf_name} (AP = {ap:.3f})'
            )
        
        ax.set_xlabel('Recall', fontsize=11)
        ax.set_ylabel('Precision', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_radar_chart(
        self,
        results: Dict[str, Dict[str, float]],
        metrics: List[str] = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc', 'fpr'],
        title: str = "Multi-Metric Performance Comparison",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Create radar chart for multi-metric comparison.
        
        Args:
            results: Dictionary mapping classifier names to metric dictionaries
            metrics: List of metrics to include
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        # Number of metrics
        n_metrics = len(metrics)
        
        # Compute angles
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        for i, (clf_name, clf_metrics) in enumerate(results.items()):
            # Get values (invert FPR so higher is better)
            values = []
            for m in metrics:
                val = clf_metrics.get(m, 0)
                if m == 'fpr':
                    val = 1 - val  # Invert FPR
                values.append(val)
            values += values[:1]  # Complete the circle
            
            ax.plot(
                angles, values,
                'o-',
                linewidth=self.config.line_width,
                markersize=self.config.marker_size,
                color=self.config.accent_colors[i % len(self.config.accent_colors)],
                label=clf_name
            )
            ax.fill(
                angles, values,
                alpha=0.15,
                color=self.config.accent_colors[i % len(self.config.accent_colors)]
            )
        
        # Set labels
        ax.set_xticks(angles[:-1])
        labels = [m.replace('_', ' ').upper() if m != 'fpr' else '1 - FPR' for m in metrics]
        ax.set_xticklabels(labels, fontsize=10)
        
        ax.set_ylim(0, 1)
        ax.set_title(title, fontsize=12, fontweight='bold', y=1.08)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_confusion_matrices(
        self,
        confusion_matrices: Dict[str, np.ndarray],
        class_labels: List[str] = ['Normal', 'Attack'],
        title: str = "Confusion Matrices Comparison",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Plot confusion matrices for multiple classifiers.
        
        Args:
            confusion_matrices: Dictionary mapping classifier names to confusion matrices
            class_labels: Labels for classes
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        n_classifiers = len(confusion_matrices)
        n_cols = min(3, n_classifiers)
        n_rows = (n_classifiers + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4*n_cols, 4*n_rows))
        if n_classifiers == 1:
            axes = np.array([axes])
        axes = axes.flatten()
        
        for i, (clf_name, cm) in enumerate(confusion_matrices.items()):
            # Normalize confusion matrix
            cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            
            sns.heatmap(
                cm_norm,
                annot=True,
                fmt='.2%',
                cmap='Blues',
                xticklabels=class_labels,
                yticklabels=class_labels,
                ax=axes[i],
                cbar=False
            )
            
            axes[i].set_title(clf_name, fontsize=11, fontweight='bold')
            axes[i].set_xlabel('Predicted', fontsize=10)
            axes[i].set_ylabel('Actual', fontsize=10)
        
        # Hide unused subplots
        for j in range(i + 1, len(axes)):
            axes[j].set_visible(False)
        
        fig.suptitle(title, fontsize=12, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def _save_figure(self, fig: Figure, path: str):
        """Save figure in specified format."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        full_path = f"{self.config.output_dir}/{path}"
        
        fig.savefig(f"{full_path}.{self.config.save_format}", 
                   dpi=self.config.dpi, bbox_inches='tight')
        fig.savefig(f"{full_path}.png", dpi=self.config.dpi, bbox_inches='tight')
        
        logger.info(f"Figure saved to {full_path}.{self.config.save_format}")


class StatisticalVisualization:
    """
    Visualization tools for statistical analysis results.
    
    Creates:
    - Significance test visualizations
    - Confidence interval plots
    - Effect size comparisons
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
    
    def plot_significance_matrix(
        self,
        p_values: pd.DataFrame,
        significance_level: float = 0.05,
        title: str = "Statistical Significance Matrix",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Plot matrix showing pairwise significance between methods.
        
        Args:
            p_values: DataFrame of p-values from pairwise tests
            significance_level: Threshold for significance
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create annotation matrix
        annot = p_values.copy()
        for i in range(len(p_values)):
            for j in range(len(p_values.columns)):
                if i == j:
                    annot.iloc[i, j] = '-'
                elif p_values.iloc[i, j] < 0.001:
                    annot.iloc[i, j] = '***'
                elif p_values.iloc[i, j] < 0.01:
                    annot.iloc[i, j] = '**'
                elif p_values.iloc[i, j] < significance_level:
                    annot.iloc[i, j] = '*'
                else:
                    annot.iloc[i, j] = 'ns'
        
        # Create heatmap
        sns.heatmap(
            p_values,
            annot=annot,
            fmt='',
            cmap='RdYlGn_r',
            center=significance_level,
            vmin=0,
            vmax=0.1,
            linewidths=0.5,
            ax=ax,
            cbar_kws={'label': 'p-value'}
        )
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Add legend
        legend_text = f'* p < {significance_level}\n** p < 0.01\n*** p < 0.001\nns: not significant'
        ax.text(
            1.02, 0.5, legend_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='center'
        )
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_confidence_intervals(
        self,
        results: Dict[str, Tuple[float, float, float]],  # (mean, lower, upper)
        metric: str = 'F1 Score',
        title: str = "Performance with 95% Confidence Intervals",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Plot confidence intervals for multiple methods.
        
        Args:
            results: Dictionary mapping method names to (mean, lower, upper) tuples
            metric: Name of the metric
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        methods = list(results.keys())
        means = [results[m][0] for m in methods]
        lowers = [results[m][1] for m in methods]
        uppers = [results[m][2] for m in methods]
        
        # Calculate error bars
        yerr = np.array([
            [m - l for m, l in zip(means, lowers)],
            [u - m for m, u in zip(means, uppers)]
        ])
        
        x = range(len(methods))
        
        # Create bar plot with error bars
        bars = ax.bar(
            x, means,
            color=self.config.accent_colors[:len(methods)],
            edgecolor='black',
            linewidth=0.5,
            capsize=self.config.error_bar_capsize,
            yerr=yerr,
            error_kw={'linewidth': 1.5, 'capthick': 1.5}
        )
        
        # Add value labels
        for bar, mean in zip(bars, means):
            ax.text(
                bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.02,
                f'{mean:.3f}',
                ha='center', va='bottom',
                fontsize=9
            )
        
        ax.set_xlabel('Method', fontsize=11)
        ax.set_ylabel(metric, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(methods, rotation=45, ha='right')
        ax.set_ylim(0, max(uppers) * 1.15)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def plot_effect_sizes(
        self,
        effect_sizes: Dict[str, Tuple[float, str]],  # (effect_size, interpretation)
        title: str = "Effect Size Analysis (Cohen's d)",
        save_path: Optional[str] = None
    ) -> Figure:
        """
        Plot effect sizes with interpretation.
        
        Args:
            effect_sizes: Dictionary mapping comparisons to (effect_size, interpretation)
            title: Plot title
            save_path: Path to save figure
        
        Returns:
            matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        comparisons = list(effect_sizes.keys())
        values = [effect_sizes[c][0] for c in comparisons]
        
        # Color by effect size magnitude
        colors = []
        for v in values:
            if abs(v) >= 0.8:
                colors.append('#C73E1D')  # Large - red
            elif abs(v) >= 0.5:
                colors.append('#F18F01')  # Medium - orange
            else:
                colors.append('#2E86AB')  # Small - blue
        
        # Create bar chart
        bars = ax.bar(
            range(len(comparisons)), values,
            color=colors,
            edgecolor='black',
            linewidth=0.5
        )
        
        # Add reference lines
        ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.5, label='Large (0.8)')
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Medium (0.5)')
        ax.axhline(y=0.2, color='blue', linestyle='--', alpha=0.5, label='Small (0.2)')
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        ax.set_xlabel('Comparison', fontsize=11)
        ax.set_ylabel("Cohen's d", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xticks(range(len(comparisons)))
        ax.set_xticklabels(comparisons, rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def _save_figure(self, fig: Figure, path: str):
        """Save figure in specified format."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        full_path = f"{self.config.output_dir}/{path}"
        
        fig.savefig(f"{full_path}.{self.config.save_format}", 
                   dpi=self.config.dpi, bbox_inches='tight')
        fig.savefig(f"{full_path}.png", dpi=self.config.dpi, bbox_inches='tight')
        
        logger.info(f"Figure saved to {full_path}.{self.config.save_format}")


class PublicationTableGenerator:
    """
    Generate publication-ready tables in LaTeX format.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
    
    def generate_results_table(
        self,
        results: Dict[str, Dict[str, float]],
        metrics: List[str] = ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc'],
        caption: str = "Performance comparison of DDoS detection methods",
        label: str = "tab:results",
        highlight_best: bool = True
    ) -> str:
        """
        Generate LaTeX table for results.
        
        Args:
            results: Dictionary mapping method names to metric dictionaries
            metrics: List of metrics to include
            caption: Table caption
            label: LaTeX label for references
            highlight_best: Whether to highlight best values
        
        Returns:
            LaTeX table string
        """
        # Find best values for each metric
        best_values = {}
        if highlight_best:
            for metric in metrics:
                best_values[metric] = max(
                    results[m].get(metric, 0) for m in results.keys()
                )
        
        # Generate LaTeX
        latex = []
        latex.append(r"\begin{table}[htbp]")
        latex.append(r"\centering")
        latex.append(r"\caption{" + caption + "}")
        latex.append(r"\label{" + label + "}")
        latex.append(r"\begin{tabular}{l" + "c" * len(metrics) + "}")
        latex.append(r"\toprule")
        
        # Header
        header = ["Method"] + [m.replace('_', ' ').title() for m in metrics]
        latex.append(" & ".join(header) + r" \\")
        latex.append(r"\midrule")
        
        # Data rows
        for method, method_metrics in results.items():
            row = [method]
            for metric in metrics:
                val = method_metrics.get(metric, 0)
                if highlight_best and val == best_values.get(metric):
                    row.append(r"\textbf{" + f"{val:.4f}" + "}")
                else:
                    row.append(f"{val:.4f}")
            latex.append(" & ".join(row) + r" \\")
        
        latex.append(r"\bottomrule")
        latex.append(r"\end{tabular}")
        latex.append(r"\end{table}")
        
        return "\n".join(latex)
    
    def generate_ablation_table(
        self,
        results: pd.DataFrame,
        caption: str = "Ablation study results",
        label: str = "tab:ablation"
    ) -> str:
        """
        Generate LaTeX table for ablation study results.
        
        Args:
            results: DataFrame with ablation results
            caption: Table caption
            label: LaTeX label
        
        Returns:
            LaTeX table string
        """
        latex = []
        latex.append(r"\begin{table}[htbp]")
        latex.append(r"\centering")
        latex.append(r"\caption{" + caption + "}")
        latex.append(r"\label{" + label + "}")
        latex.append(r"\begin{tabular}{lcccc}")
        latex.append(r"\toprule")
        latex.append(r"Component Removed & F1 Score & Accuracy & Drop (\%) & Importance \\")
        latex.append(r"\midrule")
        
        for _, row in results.iterrows():
            component = row.get('component_removed', row.get('weight_removed', 'Unknown'))
            f1 = row.get('f1_score', row.get('f1', 0))
            acc = row.get('accuracy', 0)
            drop = row.get('performance_drop', 0)
            
            # Determine importance
            if drop > 5:
                importance = "Critical"
            elif drop > 3:
                importance = "Important"
            elif drop > 1:
                importance = "Moderate"
            else:
                importance = "Minor"
            
            latex.append(f"{component} & {f1:.4f} & {acc:.4f} & {drop:.2f} & {importance} \\\\")
        
        latex.append(r"\bottomrule")
        latex.append(r"\end{tabular}")
        latex.append(r"\end{table}")
        
        return "\n".join(latex)
    
    def save_latex_table(self, latex: str, filename: str):
        """Save LaTeX table to file."""
        import os
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        path = f"{self.config.output_dir}/{filename}.tex"
        with open(path, 'w') as f:
            f.write(latex)
        
        logger.info(f"LaTeX table saved to {path}")


class ExperimentVisualizer:
    """
    Main class for comprehensive experiment visualization.
    
    Coordinates all visualization types and provides unified interface.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        
        self.ablation_viz = AblationVisualizer(config)
        self.baseline_viz = BaselineComparisonVisualizer(config)
        self.stat_viz = StatisticalVisualization(config)
        self.table_gen = PublicationTableGenerator(config)
    
    def visualize_ablation_study(
        self,
        results: Dict[str, pd.DataFrame],
        output_prefix: str = "ablation"
    ) -> Dict[str, Figure]:
        """
        Create all ablation study visualizations.
        
        Args:
            results: Dictionary of DataFrames with ablation results
            output_prefix: Prefix for output files
        
        Returns:
            Dictionary of figure names to Figure objects
        """
        figures = {}
        
        # Component importance for each category
        for category, df in results.items():
            fig = self.ablation_viz.plot_component_importance(
                df,
                title=f"{category.title()} Component Importance",
                save_path=f"{output_prefix}_{category}_importance"
            )
            figures[f'{category}_importance'] = fig
        
        # Combined comparison
        fig = self.ablation_viz.plot_ablation_comparison(
            results,
            title="Ablation Study: Performance Comparison",
            save_path=f"{output_prefix}_comparison"
        )
        figures['comparison'] = fig
        
        # Heatmap
        fig = self.ablation_viz.plot_importance_heatmap(
            results,
            title="Component Importance Heatmap",
            save_path=f"{output_prefix}_heatmap"
        )
        figures['heatmap'] = fig
        
        return figures
    
    def visualize_baseline_comparison(
        self,
        results: Dict[str, Dict[str, float]],
        roc_data: Optional[Dict[str, Tuple[np.ndarray, np.ndarray, float]]] = None,
        confusion_matrices: Optional[Dict[str, np.ndarray]] = None,
        output_prefix: str = "baseline"
    ) -> Dict[str, Figure]:
        """
        Create all baseline comparison visualizations.
        
        Args:
            results: Dictionary mapping classifier names to metrics
            roc_data: Optional ROC curve data
            confusion_matrices: Optional confusion matrices
            output_prefix: Prefix for output files
        
        Returns:
            Dictionary of figure names to Figure objects
        """
        figures = {}
        
        # Performance comparison
        fig = self.baseline_viz.plot_performance_comparison(
            results,
            title="Classifier Performance Comparison",
            save_path=f"{output_prefix}_performance"
        )
        figures['performance'] = fig
        
        # Radar chart
        fig = self.baseline_viz.plot_radar_chart(
            results,
            title="Multi-Metric Performance Radar",
            save_path=f"{output_prefix}_radar"
        )
        figures['radar'] = fig
        
        # ROC curves if provided
        if roc_data:
            fig = self.baseline_viz.plot_roc_curves(
                roc_data,
                title="ROC Curve Comparison",
                save_path=f"{output_prefix}_roc"
            )
            figures['roc'] = fig
        
        # Confusion matrices if provided
        if confusion_matrices:
            fig = self.baseline_viz.plot_confusion_matrices(
                confusion_matrices,
                title="Confusion Matrices",
                save_path=f"{output_prefix}_confusion"
            )
            figures['confusion'] = fig
        
        return figures
    
    def generate_publication_tables(
        self,
        baseline_results: Dict[str, Dict[str, float]],
        ablation_results: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, str]:
        """
        Generate all publication tables.
        
        Args:
            baseline_results: Baseline classifier results
            ablation_results: Ablation study results
        
        Returns:
            Dictionary of table names to LaTeX strings
        """
        tables = {}
        
        # Main results table
        latex = self.table_gen.generate_results_table(
            baseline_results,
            caption="Performance comparison of DDoS detection methods",
            label="tab:main_results"
        )
        tables['main_results'] = latex
        self.table_gen.save_latex_table(latex, "main_results")
        
        # Ablation tables
        if ablation_results:
            for category, df in ablation_results.items():
                latex = self.table_gen.generate_ablation_table(
                    df,
                    caption=f"{category.title()} Ablation Study Results",
                    label=f"tab:ablation_{category}"
                )
                tables[f'ablation_{category}'] = latex
                self.table_gen.save_latex_table(latex, f"ablation_{category}")
        
        return tables


def create_demo_visualizations():
    """Create demonstration visualizations with sample data."""
    print("Creating Demo Visualizations")
    print("=" * 60)
    
    # Initialize visualizer
    config = VisualizationConfig(
        output_dir="./results/figures",
        save_format="pdf"
    )
    visualizer = ExperimentVisualizer(config)
    
    # Create sample baseline results
    baseline_results = {
        'Knowledge Graph': {
            'accuracy': 0.942, 'precision': 0.938, 'recall': 0.946,
            'f1_score': 0.942, 'auc_roc': 0.967, 'fpr': 0.018
        },
        'Random Forest': {
            'accuracy': 0.891, 'precision': 0.885, 'recall': 0.898,
            'f1_score': 0.891, 'auc_roc': 0.923, 'fpr': 0.042
        },
        'XGBoost': {
            'accuracy': 0.912, 'precision': 0.908, 'recall': 0.916,
            'f1_score': 0.912, 'auc_roc': 0.945, 'fpr': 0.031
        },
        'LSTM': {
            'accuracy': 0.878, 'precision': 0.872, 'recall': 0.885,
            'f1_score': 0.878, 'auc_roc': 0.901, 'fpr': 0.055
        },
        'GCN': {
            'accuracy': 0.923, 'precision': 0.918, 'recall': 0.928,
            'f1_score': 0.923, 'auc_roc': 0.956, 'fpr': 0.025
        }
    }
    
    # Create sample ROC data
    np.random.seed(42)
    roc_data = {}
    for clf_name, metrics in baseline_results.items():
        auc = metrics['auc_roc']
        fpr = np.linspace(0, 1, 100)
        tpr = np.power(fpr, 1 - auc) * auc + fpr * (1 - auc) + np.random.normal(0, 0.01, 100)
        tpr = np.clip(tpr, 0, 1)
        roc_data[clf_name] = (fpr, tpr, auc)
    
    # Create sample ablation results
    ablation_results = {
        'ontology': pd.DataFrame([
            {'component_removed': 'http_entities', 'f1_score': 0.884, 'accuracy': 0.892, 'performance_drop': 5.13},
            {'component_removed': 'dns_entities', 'f1_score': 0.904, 'accuracy': 0.912, 'performance_drop': 3.03},
            {'component_removed': 'session_entities', 'f1_score': 0.859, 'accuracy': 0.867, 'performance_drop': 8.28},
            {'component_removed': 'attack_entities', 'f1_score': 0.894, 'accuracy': 0.902, 'performance_drop': 4.07},
            {'component_removed': 'mitigation_entities', 'f1_score': 0.924, 'accuracy': 0.932, 'performance_drop': 1.07},
            {'component_removed': 'behavior_entities', 'f1_score': 0.878, 'accuracy': 0.886, 'performance_drop': 6.03}
        ]),
        'rules': pd.DataFrame([
            {'component_removed': 'volume_rules', 'f1_score': 0.894, 'accuracy': 0.902, 'performance_drop': 4.28},
            {'component_removed': 'structural_rules', 'f1_score': 0.914, 'accuracy': 0.922, 'performance_drop': 2.14},
            {'component_removed': 'behavioral_rules', 'f1_score': 0.874, 'accuracy': 0.882, 'performance_drop': 6.42},
            {'component_removed': 'intelligence_rules', 'f1_score': 0.904, 'accuracy': 0.912, 'performance_drop': 3.21}
        ]),
        'weights': pd.DataFrame([
            {'weight_removed': 'alpha', 'f1_score': 0.904, 'accuracy': 0.912, 'performance_drop': 3.21},
            {'weight_removed': 'beta', 'f1_score': 0.919, 'accuracy': 0.927, 'performance_drop': 1.61},
            {'weight_removed': 'gamma', 'f1_score': 0.894, 'accuracy': 0.902, 'performance_drop': 4.28},
            {'weight_removed': 'delta', 'f1_score': 0.914, 'accuracy': 0.922, 'performance_drop': 2.14}
        ])
    }
    
    # Create visualizations
    print("\n1. Creating Baseline Comparison Visualizations...")
    figures = visualizer.visualize_baseline_comparison(
        baseline_results,
        roc_data=roc_data,
        output_prefix="demo_baseline"
    )
    print(f"   Created {len(figures)} figures")
    
    print("\n2. Creating Ablation Study Visualizations...")
    figures = visualizer.visualize_ablation_study(
        ablation_results,
        output_prefix="demo_ablation"
    )
    print(f"   Created {len(figures)} figures")
    
    print("\n3. Generating Publication Tables...")
    tables = visualizer.generate_publication_tables(
        baseline_results,
        ablation_results
    )
    print(f"   Generated {len(tables)} LaTeX tables")
    
    print("\n" + "=" * 60)
    print("Demo visualizations created successfully!")
    print(f"Output directory: {config.output_dir}")
    
    return figures, tables


if __name__ == "__main__":
    create_demo_visualizations()
