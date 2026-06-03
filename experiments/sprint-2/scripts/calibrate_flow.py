#!/usr/bin/env python3
"""Calibra distribuições de fluxo POR-REQUISIÇÃO a partir de sessões benignas REAIS.

O gerador emite eventos (requisições); para que as sessões sintéticas carreguem
features de volume realistas (fwd/bwd bytes e pacotes), amostramos, por requisição,
de quantis empíricos derivados do tráfego benigno real (sum/n_requests por sessão).

Crucial para a tese: no cenário furtivo, sessões atacantes amostram DAS MESMAS
distribuições benignas — assim um ML por-sessão COMPLETO (8 features) não as separa,
e só a coordenação cross-session trai a campanha. Sem isto, a vantagem cross-session
seria artefato de um baseline por-sessão sub-dimensionado.

Uso:
    python calibrate_flow.py --benign /.../cicids2017.parquet \\
        --out-dir $DATA/synth/distributions
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# métrica por-requisição = coluna_de_sessão / n_requests
PER_REQ = {
    "flow_fwd_bytes": "fwd_bytes_sum",
    "flow_bwd_bytes": "bwd_bytes_sum",
    "flow_fwd_pkts": "fwd_pkts_sum",
    "flow_bwd_pkts": "bwd_pkts_sum",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--benign", required=True, type=Path,
                    help="parquet de sessões reais (usa só label_first==BENIGN)")
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    df = pd.read_parquet(args.benign)
    b = df[df["label_first"] == "BENIGN"].copy()
    nreq = b["n_requests"].clip(lower=1)
    qs = np.linspace(0, 1, 101)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, col in PER_REQ.items():
        per_req = (b[col].fillna(0).clip(lower=0) / nreq).to_numpy()
        quant = np.quantile(per_req, qs).tolist()
        (args.out_dir / f"{name}.json").write_text(json.dumps({
            "metric": f"{col}/n_requests (benign, real)",
            "n_benign_sessions": int(len(b)),
            "median": float(np.median(per_req)),
            "quantiles": quant,
        }, indent=2))
        print(f"{name}: mediana={np.median(per_req):.1f} p99={np.quantile(per_req,0.99):.1f} "
              f"(de {len(b)} sessões benignas reais) → {args.out_dir/f'{name}.json'}")


if __name__ == "__main__":
    main()
