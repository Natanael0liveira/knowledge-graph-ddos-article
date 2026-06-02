#!/usr/bin/env python3
"""Three academic baselines for L7-DDoS / anomalous-session detection.

All operate on PER-SESSION behavioral features only (no cross-session structure)
— that is the point of the comparison: they are blind to the relatedBy_* family,
so the ablation's full config (d) should beat them on distributed scenarios (B/C)
while matching them on the concentrated scenario (A). See Sprint-3 plan.

These are faithful *operationalizations* of the published methods (the original
papers' exact hyperparameters are not all recoverable); each returns an anomaly
score in [0,1] per session so we can compute ROC AUC against ground truth.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def fernandes2015(Xtr, Xte, ytr=None):
    """Fernandes 2015 — PCA + reconstruction-error thresholding (unsupervised).

    Project to top-k PCs, reconstruct, score = reconstruction error. Anomalies
    (attacks) reconstruct poorly. Unsupervised — ignores ytr.
    """
    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)
    k = max(1, min(Xtr_s.shape[1] - 1, 3))
    pca = PCA(n_components=k).fit(Xtr_s)
    recon = pca.inverse_transform(pca.transform(Xte_s))
    err = np.sqrt(((Xte_s - recon) ** 2).sum(axis=1))
    # normalize to [0,1]
    return (err - err.min()) / (err.ptp() + 1e-9)


def bharathi2012(Xtr, Xte, ytr=None):
    """Bharathi 2012 — k-means on the behavioral matrix (unsupervised).

    Cluster; the smaller cluster is assumed anomalous; score = distance-weighted
    membership to the anomalous cluster. Unsupervised.
    """
    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)
    km = KMeans(n_clusters=2, n_init=10, random_state=42).fit(Xtr_s)
    sizes = np.bincount(km.labels_, minlength=2)
    anom = int(np.argmin(sizes))  # smaller cluster = anomalous
    d = km.transform(Xte_s)  # distance to each centroid
    # score high when close to anomalous centroid and far from normal one
    score = d[:, 1 - anom] - d[:, anom]
    return (score - score.min()) / (score.ptp() + 1e-9)


def kemp2023(Xtr, Xte, ytr):
    """Kemp 2023 — supervised Random Forest + SVM ensemble.

    Average of RF and (probability-calibrated) SVM scores. Supervised.
    """
    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)
    rf = RandomForestClassifier(n_estimators=200, random_state=42,
                                class_weight="balanced", n_jobs=-1).fit(Xtr, ytr)
    svm = SVC(probability=True, class_weight="balanced",
              random_state=42).fit(Xtr_s, ytr)
    p_rf = rf.predict_proba(Xte)[:, 1]
    p_svm = svm.predict_proba(Xte_s)[:, 1]
    return (p_rf + p_svm) / 2.0


BASELINES = {
    "fernandes2015": (fernandes2015, "PCA + limiarização (não-supervisionado)"),
    "bharathi2012": (bharathi2012, "k-means comportamental (não-supervisionado)"),
    "kemp2023": (kemp2023, "RandomForest + SVM (supervisionado)"),
}
