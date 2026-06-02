#!/usr/bin/env python3
"""Extrai distribuições estatísticas do tráfego legítimo do Sprint 1.

Lê sessions.parquet, filtra apenas sessões BENIGN, e produz JSONs com
distribuições que servirão para amostrar tráfego legítimo sintético no
gerador (generator.py).

Distribuições produzidas:
- session_duration.json   : duração das sessões (s)
- session_requests.json   : número de requisições por sessão
- ja4_users.json          : distribuição de JA4 entre usuários legítimos
- endpoints.json          : distribuição de endpoints visitados
- arrival.json            : padrão temporal de chegada de sessões (IAT)

Usage:
    python calibrate.py --sessions sessions.parquet --out-dir distributions/
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def filter_benign(sessions: pd.DataFrame) -> pd.DataFrame:
    """Filtra apenas sessões legítimas (BENIGN)."""
    label_col = "label_first" if "label_first" in sessions.columns else "label"
    if label_col not in sessions.columns:
        log.error("Coluna de label não encontrada.")
        sys.exit(1)
    # CICIDS2017 usa "BENIGN" como rótulo de tráfego normal
    benign = sessions[sessions[label_col].str.upper() == "BENIGN"]
    log.info("Sessões legítimas: %d (de %d totais)", len(benign), len(sessions))
    return benign


def extract_numeric_distribution(values: pd.Series, n_bins: int = 50) -> dict:
    """Resumo de distribuição numérica via histograma + percentis."""
    values = values.dropna()
    if len(values) == 0:
        return {"count": 0}
    hist, edges = np.histogram(values, bins=n_bins)
    # Quantis empíricos (inverse-CDF) — reproduzem fielmente distribuições muito
    # concentradas (duração ~0, n_requests ~1) que o histograma de bins largos
    # borraria. O gerador amostra via estes quantis.
    quantiles = np.quantile(values, np.linspace(0.0, 1.0, 1001)).tolist()
    return {
        "count": int(len(values)),
        "min": float(values.min()),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "p10": float(values.quantile(0.10)),
        "p25": float(values.quantile(0.25)),
        "p75": float(values.quantile(0.75)),
        "p90": float(values.quantile(0.90)),
        "p99": float(values.quantile(0.99)),
        "std": float(values.std()),
        "quantiles": quantiles,
        "histogram": {
            "edges": edges.tolist(),
            "counts": hist.tolist(),
        },
    }


def extract_categorical_distribution(values: pd.Series, top_k: int = 100) -> dict:
    """Distribuição categórica: top-K valores e suas frequências."""
    counts = values.dropna().value_counts().head(top_k)
    total = counts.sum()
    return {
        "total": int(total),
        "unique": int(values.dropna().nunique()),
        "top_k": int(top_k),
        "distribution": [
            {"value": str(k), "count": int(v), "frequency": float(v / total)}
            for k, v in counts.items()
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    sessions = pd.read_parquet(args.sessions)
    log.info("Carregadas %d sessões de %s", len(sessions), args.sessions)

    benign = filter_benign(sessions)
    if len(benign) == 0:
        log.error("Nenhuma sessão BENIGN encontrada. Calibração não é possível.")
        sys.exit(1)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Duração das sessões — condicionada a n_req≥2.
    # No real, sessões de 1 request têm duração 0 (sem span); a duração>0 vive nas
    # multi-request. O gerador dá span 0 a n_req=1 e amostra ESTA distribuição para
    # n_req≥2, preservando a correlação duração⇔n_req (senão o gate KS de duração falha).
    if "duration_s" in benign.columns:
        multi = benign[benign["n_requests"] >= 2] if "n_requests" in benign.columns else benign
        dist = extract_numeric_distribution(multi["duration_s"])
        (args.out_dir / "session_duration.json").write_text(json.dumps(dist, indent=2))
        log.info("Duração (n_req≥2, n=%d): mean=%.1fs, median=%.1fs",
                 len(multi), dist.get("mean", 0), dist.get("median", 0))

    # 2. Requisições por sessão
    if "n_requests" in benign.columns:
        dist = extract_numeric_distribution(benign["n_requests"])
        (args.out_dir / "session_requests.json").write_text(json.dumps(dist, indent=2))
        log.info("Requisições/sessão: mean=%.1f, median=%.1f",
                 dist.get("mean", 0), dist.get("median", 0))

    # 3. JA4 entre legítimos
    if "ja4" in benign.columns:
        dist = extract_categorical_distribution(benign["ja4"])
        (args.out_dir / "ja4_users.json").write_text(json.dumps(dist, indent=2))
        log.info("JA4 únicos entre legítimos: %d", dist.get("unique", 0))

    # 4. Endpoints
    if "dst_port_first" in benign.columns or "dst_port" in benign.columns:
        col = "dst_port_first" if "dst_port_first" in benign.columns else "dst_port"
        dist = extract_categorical_distribution(benign[col])
        (args.out_dir / "endpoints.json").write_text(json.dumps(dist, indent=2))
        log.info("Portas únicas: %d", dist.get("unique", 0))

    # 5. Padrão temporal de chegada (IAT entre sessões consecutivas)
    if "start_ts" in benign.columns:
        starts = pd.to_datetime(benign["start_ts"]).sort_values()
        iat = starts.diff().dt.total_seconds().dropna()
        dist = extract_numeric_distribution(iat)
        (args.out_dir / "arrival.json").write_text(json.dumps(dist, indent=2))
        log.info("IAT entre chegadas: mean=%.2fs, median=%.2fs",
                 dist.get("mean", 0), dist.get("median", 0))

    # 6. Metadata
    metadata = {
        "source": str(args.sessions),
        "total_sessions": int(len(sessions)),
        "benign_sessions": int(len(benign)),
        "label_distribution": sessions["label_first" if "label_first" in sessions.columns else "label"].value_counts().to_dict() if "label_first" in sessions.columns or "label" in sessions.columns else {},
        "files_produced": [
            "session_duration.json",
            "session_requests.json",
            "ja4_users.json",
            "endpoints.json",
            "arrival.json",
        ],
    }
    (args.out_dir / "_metadata.json").write_text(json.dumps(metadata, indent=2))
    log.info("✅ Calibração concluída. %d arquivos em %s",
             len(metadata["files_produced"]) + 1, args.out_dir)


if __name__ == "__main__":
    main()
