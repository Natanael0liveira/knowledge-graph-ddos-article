#!/usr/bin/env python3
"""Gerador sintético de tráfego HTTP para os Cenários A, B, C.

Produz um stream JSONL com eventos HTTP estruturados: tráfego legítimo
calibrado pelas distribuições de Sprint 1 + campanha de ataque coordenado
parametrizada por K (grau de distribuição).

Saída: arquivo JSONL pronto para ingestão pelo pipeline do Sprint 1.

Usage:
    python generator.py --config configs/scenario_C.yaml \\
                        --seed 42 \\
                        --param K=1000 \\
                        --distributions $DATA_ROOT/synth/distributions \\
                        --out output.jsonl
"""
import argparse
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def load_distributions(dist_dir: Path) -> dict:
    """Carrega distribuições calibradas (saída de calibrate.py)."""
    dists = {}
    for fname in ["session_duration", "session_requests", "ja4_users",
                  "endpoints", "arrival"]:
        path = dist_dir / f"{fname}.json"
        if path.exists():
            dists[fname] = json.loads(path.read_text())
        else:
            log.warning("Distribuição %s não encontrada em %s", fname, path)
    return dists


def sample_categorical(dist: dict, rng: random.Random):
    """Amostra de uma distribuição categórica (top-K values com frequência)."""
    if not dist or "distribution" not in dist or not dist["distribution"]:
        return None
    weights = [item["frequency"] for item in dist["distribution"]]
    values = [item["value"] for item in dist["distribution"]]
    return rng.choices(values, weights=weights, k=1)[0]


def sample_numeric(dist: dict, rng: random.Random, default: float = 0.0) -> float:
    """Amostra de uma distribuição numérica.

    Prefere inverse-CDF via quantis empíricos (fiel a distribuições concentradas);
    cai para o histograma se os quantis não existirem (calibração antiga).
    """
    if not dist:
        return default
    q = dist.get("quantiles")
    if q:
        # interpolação linear entre dois quantis vizinhos (CDF empírica suave)
        u = rng.random() * (len(q) - 1)
        lo = int(u)
        frac = u - lo
        hi = min(lo + 1, len(q) - 1)
        return q[lo] + frac * (q[hi] - q[lo])
    hist = dist.get("histogram")
    if not hist or not hist.get("counts") or sum(hist["counts"]) == 0:
        return dist.get("median", default)
    edges, counts = hist["edges"], hist["counts"]
    bin_idx = rng.choices(range(len(counts)), weights=counts, k=1)[0]
    return rng.uniform(edges[bin_idx], edges[bin_idx + 1])


def generate_legitimate_session(
    sid: str, t0: datetime, rng: random.Random, dists: dict, benign_ja4_pool: int = 0
) -> list[dict]:
    """Gera uma sessão legítima como lista de requisições HTTP.

    ``benign_ja4_pool``: se > 0, o JA4 legítimo é amostrado de um espaço de tamanho
    ``benign_ja4_pool`` (diversidade realista de navegadores/dispositivos da internet,
    milhares de fingerprints) em vez do pool pequeno (dezenas) herdado dos datasets de
    laboratório. Necessário para que o JA4 compartilhado do atacante seja discriminativo
    (do contrário, legítimos compartilham JA4 mais que a campanha — artefato de lab).
    """
    # Sem clamp distorcivo: o real tem muitas sessões de duração ~0 / 1 request;
    # forçar mínimos quebraria o casamento de distribuição (gate KS).
    duration = max(0.0, sample_numeric(dists.get("session_duration", {}), rng, 10.0))
    n_req = max(1, round(sample_numeric(dists.get("session_requests", {}), rng, 5)))
    if benign_ja4_pool and benign_ja4_pool > 0:
        ja4 = f"benign_ja4_{rng.randint(0, benign_ja4_pool - 1)}"
    else:
        ja4 = sample_categorical(dists.get("ja4_users", {}), rng) or "t13d1516h2_default"
    port = sample_categorical(dists.get("endpoints", {}), rng) or "443"

    # Clientes legítimos vêm de MUITAS redes (diversidade realista). Espaço RFC 6598
    # (100.64.0.0/10): ~16k /24s distintos → colisões de /24 raras entre as sessões,
    # como no tráfego real. Antes: todos em 192.0.2.0/24, inflando relatedByNetworkProximity.
    src_ip = f"100.{rng.randint(64, 127)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    src_port = rng.randint(30000, 60000)
    asn = rng.randint(64496, 64511)  # RFC 5398

    # Ancorar o span ao duration amostrado: 1º request em t0, último em t0+duration.
    # Sem isso, o span observado encolhe vs a duração amostrada (artefato que
    # enviesava o gate KS de duração).
    offsets = sorted(rng.uniform(0, duration) for _ in range(n_req))
    if n_req >= 2:
        offsets[0], offsets[-1] = 0.0, duration

    events = []
    for i in range(n_req):
        t = t0 + timedelta(seconds=offsets[i])
        events.append({
            "timestamp": t.isoformat() + "Z",
            "src_ip": src_ip,
            "src_port": src_port,
            "dst_ip": "10.0.0.1",
            "dst_port": int(port) if str(port).isdigit() else 443,
            "tls_ja4": ja4,
            "session_id": sid,
            "identity_token": None,
            "method": rng.choice(["GET", "GET", "GET", "POST"]),
            "path": rng.choice([
                "/", "/api/users", "/api/products", "/api/search",
                "/static/main.css", "/api/cart"
            ]),
            "headers": {"User-Agent": f"Mozilla/5.0 (synthetic-{sid})"},
            "status_code": rng.choice([200, 200, 200, 200, 304]),
            "asn": asn,
            "is_attack": False,
            "campaign_id": None,
        })
    return sorted(events, key=lambda e: e["timestamp"])


def generate_attack_session(
    sid: str,
    t0: datetime,
    rng: random.Random,
    *,
    K: int,
    attack_variant: str,
    coordination_ja4_share: float,
    coordination_identity_reuse: float,
    coordination_temporal_jitter: float,
    shared_ja4: str,
    shared_token: str,
    target_endpoint: dict,
    asn_pool: list[int],
    prefix_pool: list[str],
    campaign_id: str,
    window_s: int,
    dists: dict | None = None,
    stealth: bool = False,
) -> list[dict]:
    """Gera uma sessão atacante coordenada (parte da campanha).

    Se ``stealth``, as features POR-SESSÃO (n_req, duração, path, User-Agent) são
    amostradas das distribuições benignas — cada sessão é individualmente
    indistinguível de um usuário legítimo. A campanha só é detectável pela
    ESTRUTURA cross-session (JA4/alvo/prefixo/identidade compartilhados). É o caso
    que separa a tese do estado-da-arte: detecção por-sessão falha, cross-session acerta.
    """
    # JA4 compartilhado ou independente
    if rng.random() < coordination_ja4_share:
        ja4 = shared_ja4
    else:
        ja4 = f"t13d1516h2_unique_{rng.randint(0, 1<<16):04x}"

    # Identidade reaproveitada ou nova
    if rng.random() < coordination_identity_reuse:
        token = shared_token
    else:
        token = f"token_{rng.randint(0, 1<<32):08x}"

    # IP no pool de prefixos
    prefix = rng.choice(prefix_pool)
    src_ip = prefix + str(rng.randint(1, 254))
    src_port = rng.randint(30000, 60000)
    asn = rng.choice(asn_pool)

    dists = dists or {}
    if stealth:
        # Mimético: per-session vem do benigno; só a coordenação trai a campanha.
        n_req = max(1, round(sample_numeric(dists.get("session_requests", {}), rng, 1)))
        duration = max(0.0, sample_numeric(dists.get("session_duration", {}), rng, 0.0))
        base_iat = (duration / max(1, n_req - 1)) if n_req > 1 else 1.0
        ua = f"Mozilla/5.0 (synthetic-{sid})"
        method = rng.choice(["GET", "GET", "GET", "POST"])
    elif attack_variant in ("slowloris", "slow_body", "slow_read"):
        n_req = rng.randint(3, 8)
        base_iat = 15.0  # 1 byte/15s típico do slowloris
        duration = window_s
        ua = "slowhttptest/1.8 (synthetic)"
        method = "POST" if attack_variant in ("slowloris", "slow_body") else "GET"
    elif attack_variant in ("hulk", "goldeneye"):
        n_req = rng.randint(50, 200)
        base_iat = 0.5
        duration = min(window_s, n_req * base_iat * 1.2)
        ua = f"hulk-attack/{attack_variant}"
        method = "GET"
    else:
        n_req = 10
        base_iat = 1.0
        duration = 30.0
        ua = f"synthetic-attack/{attack_variant}"
        method = "GET"

    # Todas as origens convergem no MESMO endpoint-alvo (EndpointConvergence) —
    # sinal de coordenação preservado mesmo no modo furtivo.
    path = target_endpoint.get("path", "/api/checkout/payment")

    events = []
    t = t0
    for i in range(n_req):
        # Jitter
        jitter_factor = 1.0 + coordination_temporal_jitter * rng.uniform(-0.5, 0.5)
        delta = base_iat * jitter_factor
        t = t + timedelta(seconds=max(0.1, delta))
        if (t - t0).total_seconds() > window_s:
            break
        events.append({
            "timestamp": t.isoformat() + "Z",
            "src_ip": src_ip,
            "src_port": src_port,
            "dst_ip": "10.0.0.1",
            "dst_port": 443,
            "tls_ja4": ja4,
            "session_id": sid,
            "identity_token": token,
            "method": method,
            "path": path,
            "headers": {"User-Agent": ua},
            "status_code": 200,
            "asn": asn,
            "is_attack": True,
            "campaign_id": campaign_id,
        })
    return events


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--distributions", required=True, type=Path,
                    help="Diretório com calibração (saída de calibrate.py)")
    ap.add_argument("--param", action="append", default=[],
                    help="Override de parâmetro: --param K=1000")
    args = ap.parse_args()

    # Carregar config
    cfg = yaml.safe_load(args.config.read_text())
    # Overrides
    for p in args.param:
        k, _, v = p.partition("=")
        try:
            cfg[k] = int(v)
        except ValueError:
            try:
                cfg[k] = float(v)
            except ValueError:
                cfg[k] = v

    log.info("Config: %s", cfg)

    # RNG reprodutível
    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    # Distribuições calibradas
    dists = load_distributions(args.distributions)

    # Setup da campanha
    K = cfg.get("K", 1)
    legitimate_sessions = cfg.get("legitimate_sessions", 500)
    attack_variant = cfg.get("attack_variant", "slowloris")
    window_s = cfg.get("window_s", 300)
    coordination_ja4_share = cfg.get("coordination_ja4_share", 1.0)
    coordination_identity_reuse = cfg.get("coordination_identity_reuse", 0.0)
    coordination_temporal_jitter = cfg.get("coordination_temporal_jitter", 0.0)
    asn_dispersion = cfg.get("asn_dispersion", 1)
    prefix_dispersion = cfg.get("prefix_dispersion", 1)

    # Pools para origens coordenadas
    asn_pool = [rng.randint(64500, 64511) for _ in range(asn_dispersion)]
    # prefix_dispersion /24s DISTINTOS no espaço 10.0.0.0/8 (privado, 65k /24s).
    # Antes ciclavam só 3 prefixos → ataque "distribuído" concentrado em 3 /24s,
    # tornando NetworkProximity trivialmente forte. Com prefix_dispersion ~ K
    # (Mirai-style: ~1 bot por /24), a proximidade de rede fica fraca — como o
    # paper assume (w_net=0.3) — e o JA4 compartilhado é que carrega a detecção.
    prefix_pool = [f"10.{(i // 256) % 256}.{i % 256}." for i in range(prefix_dispersion)]

    shared_ja4 = f"t13d1516h2_synth_{args.seed:04x}"
    shared_token = f"synth_token_{args.seed:08x}"
    target_endpoint = {"path": "/api/checkout/payment"}
    campaign_id = f"synth_{args.config.stem}_seed{args.seed}"

    # Origem temporal — agora é "agora" da geração
    t_start = datetime(2026, 5, 30, 12, 0, 0)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    n_events = 0
    n_legit = 0
    n_atk = 0
    with args.out.open("w") as fout:
        # 1. Tráfego legítimo
        log.info("Gerando %d sessões legítimas...", legitimate_sessions)
        for i in range(legitimate_sessions):
            sid = f"legit_{i:06d}"
            iat = max(0.01, sample_numeric(dists.get("arrival", {}), rng, 0.5))
            t0 = t_start + timedelta(seconds=i * iat)
            for ev in generate_legitimate_session(sid, t0, rng, dists,
                                                   benign_ja4_pool=int(cfg.get("benign_ja4_pool", 0))):
                fout.write(json.dumps(ev) + "\n")
                n_events += 1
                n_legit += 1

        # 2. Tráfego de ataque coordenado (K origens)
        log.info("Gerando %d origens atacantes (variant=%s)...", K, attack_variant)
        for i in range(K):
            sid = f"attack_{i:06d}"
            # Atacantes chegam quase simultaneamente (início da campanha)
            t0 = t_start + timedelta(seconds=rng.uniform(0, 30))
            for ev in generate_attack_session(
                sid, t0, rng,
                K=K,
                attack_variant=attack_variant,
                coordination_ja4_share=coordination_ja4_share,
                coordination_identity_reuse=coordination_identity_reuse,
                coordination_temporal_jitter=coordination_temporal_jitter,
                shared_ja4=shared_ja4,
                shared_token=shared_token,
                target_endpoint=target_endpoint,
                asn_pool=asn_pool,
                prefix_pool=prefix_pool,
                campaign_id=campaign_id,
                window_s=window_s,
                dists=dists,
                stealth=bool(cfg.get("stealth", False)),
            ):
                fout.write(json.dumps(ev) + "\n")
                n_events += 1
                n_atk += 1

    log.info("✅ Gerados %d eventos: %d legítimos + %d atacantes em %s",
             n_events, n_legit, n_atk, args.out)


if __name__ == "__main__":
    main()
