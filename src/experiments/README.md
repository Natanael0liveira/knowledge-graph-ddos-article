# Experiments Module

This module contains the experimental framework for evaluating the Knowledge Graph-based DDoS detection system.

## Module Overview

### 1. `ablation_study.py` - Ablation Study Module

Comprehensive ablation study implementation to analyze the contribution of individual components to the overall system performance.

**Key Classes:**
- `AblationConfig`: Configuration for ablation study settings
- `AblationResult`: Container for ablation experiment results
- `OntologyAblator`: Ablation for ontology components (HTTP, DNS, Session entities)
- `RuleAblator`: Ablation for detection rule categories
- `WeightAblator`: Sensitivity analysis for anomaly score weights
- `AblationStudy`: Main coordinator for comprehensive ablation studies

**Usage:**
```python
from src.experiments.ablation_study import AblationStudy, AblationConfig

config = AblationConfig(
    ablate_ontology=True,
    ablate_rules=True,
    ablate_weights=True,
    save_results=True
)

study = AblationStudy(config)
results = study.run_full_ablation(X_train, y_train, X_test, y_test, baseline_f1=0.934)

# Get importance ranking
ranking = study.ontology_ablator.get_importance_ranking()
```

### 2. `visualization.py` - Experimental Results Visualization

Publication-ready visualization tools for all experimental results.

**Key Classes:**
- `VisualizationConfig`: Configuration for figure settings
- `AblationVisualizer`: Visualizations for ablation study results
- `BaselineComparisonVisualizer`: Visualizations for classifier comparisons
- `StatisticalVisualization`: Visualizations for statistical analysis
- `PublicationTableGenerator`: LaTeX table generation
- `ExperimentVisualizer`: Main coordinator for all visualizations

**Visualization Types:**
- Component importance bar charts
- Performance comparison grouped bars
- ROC curves and Precision-Recall curves
- Radar charts for multi-metric comparison
- Confusion matrix heatmaps
- Significance matrices
- Confidence interval plots

**Usage:**
```python
from src.experiments.visualization import ExperimentVisualizer, VisualizationConfig

config = VisualizationConfig(
    output_dir='./results/figures',
    save_format='pdf',
    save_latex=True
)

visualizer = ExperimentVisualizer(config)

# Visualize ablation study
figures = visualizer.visualize_ablation_study(ablation_results)

# Visualize baseline comparison
figures = visualizer.visualize_baseline_comparison(baseline_results, roc_data=roc_data)

# Generate publication tables
tables = visualizer.generate_publication_tables(baseline_results, ablation_results)
```

### 3. `baseline_classifiers.py` - Baseline Classifiers

Implementation of baseline classifiers for comparison with the Knowledge Graph approach.

**Implemented Baselines:**
- Random Forest (RF)
- XGBoost
- LSTM
- GCN (Graph Convolutional Network)
- Autoencoder

### 4. `statistical_analysis.py` - Statistical Analysis

Statistical tests and analysis for comparing methods.

**Features:**
- Paired t-tests
- Wilcoxon signed-rank tests
- McNemar's test
- Effect size calculations (Cohen's d)
- Bootstrap confidence intervals

### 5. `dataset_loader.py` - Dataset Loading

Utilities for loading and preprocessing datasets.

## Output Structure

```
results/
├── ablation/
│   ├── ontology_ablation.csv
│   ├── rules_ablation.csv
│   ├── weights_ablation.csv
│   └── ablation_report.txt
└── figures/
    ├── ablation_ontology_importance.pdf
    ├── ablation_comparison.pdf
    ├── ablation_heatmap.pdf
    ├── baseline_performance.pdf
    ├── baseline_roc.pdf
    ├── baseline_radar.pdf
    ├── main_results.tex
    └── ablation_*.tex
```

## Configuration Options

### AblationConfig
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ablate_ontology` | bool | True | Enable ontology component ablation |
| `ablate_rules` | bool | True | Enable detection rule ablation |
| `ablate_weights` | bool | True | Enable weight sensitivity analysis |
| `ablate_enrichment` | bool | True | Enable enrichment ablation |
| `full_factorial` | bool | False | Test all combinations |
| `leave_one_out` | bool | True | Use leave-one-out approach |
| `save_results` | bool | True | Save results to files |
| `output_dir` | str | "./results/ablation" | Output directory |

### VisualizationConfig
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `figsize` | tuple | (10, 6) | Figure size |
| `dpi` | int | 300 | Resolution |
| `style` | str | 'seaborn-v0_8-whitegrid' | Matplotlib style |
| `color_palette` | str | 'colorblind' | Seaborn color palette |
| `output_dir` | str | './results/figures' | Output directory |
| `save_format` | str | 'pdf' | Output format (pdf, png, svg, eps) |
| `save_latex` | bool | True | Generate LaTeX tables |

## Dependencies

```
numpy>=1.20.0
pandas>=1.3.0
matplotlib>=3.4.0
seaborn>=0.11.0
scikit-learn>=0.24.0
```

## Example: Complete Experiment Pipeline

```python
import numpy as np
from src.experiments.ablation_study import AblationStudy, AblationConfig
from src.experiments.visualization import ExperimentVisualizer, VisualizationConfig
from src.experiments.baseline_classifiers import run_baseline_comparison
from src.experiments.statistical_analysis import StatisticalAnalyzer

# 1. Run baseline comparison
baseline_results = run_baseline_comparison(X_train, y_train, X_test, y_test)

# 2. Run ablation study
ablation_config = AblationConfig(save_results=True)
ablation_study = AblationStudy(ablation_config)
ablation_results = ablation_study.run_full_ablation(
    X_train, y_train, X_test, y_test, baseline_f1=0.934
)

# 3. Statistical analysis
analyzer = StatisticalAnalyzer()
stat_results = analyzer.comprehensive_comparison(baseline_results)

# 4. Generate visualizations
viz_config = VisualizationConfig(output_dir='./results/figures')
visualizer = ExperimentVisualizer(viz_config)

# Create all visualizations
visualizer.visualize_ablation_study(ablation_results)
visualizer.visualize_baseline_comparison(baseline_results['metrics'])
visualizer.generate_publication_tables(baseline_results['metrics'], ablation_results)

print("Experiment pipeline completed!")
```

## Publication-Ready Output

The visualization module generates LaTeX-compatible output:

**Tables:**
- Uses `booktabs` package for professional formatting
- Highlights best values in bold
- Includes proper captions and labels

**Figures:**
- 300 DPI resolution
- Times New Roman font family
- Colorblind-friendly palette
- PDF format for LaTeX integration

## References

- Meyes, R., et al. (2019). "Ablation Studies in Deep Neural Networks."
- Breiman, L. (2001). "Random Forests." Machine Learning, 45(1), 5-32.
- Chen, T., & Guestrin, C. (2016). "XGBoost: A Scalable Tree Boosting System." KDD.
- Kipf, T. N., & Welling, M. (2017). "Semi-Supervised Classification with GCNs." ICLR.
