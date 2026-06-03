# Sprint 2 — Gerador Sintético Calibrado

> **Objetivo:** gerar tráfego sintético parametrizado pelo grau de distribuição $K$, calibrado a partir das distribuições reais extraídas no Sprint 1, para permitir avaliação experimental dos Cenários A (concentrado, $K=1$), B (moderado, $K=10\text{–}100$) e C (distribuído, $K \ge 1000$).

> **Status:** 🛠 Esqueleto. A calibração depende dos *outputs* do Sprint 1.

## Por que precisamos de tráfego sintético

A *ground truth* de cluster necessária para a métrica de *recall por campanha* e para a ablação **(c)** (apenas `relatedByNetworkProximity`) versus **(d)** (família completa) **não existe nos *datasets* públicos**. Os labels do CICIDS2017 são por flow, não por campanha coordenada. O gerador sintético resolve isso:

- Cada execução produz uma campanha com *ground truth* perfeitamente conhecida
- $K$ controlado: A ($K=1$), B (10–100), C (≥ 1000)
- Calibração contra dados reais garante realismo (rejeita inflação artificial)

## Princípio de calibração

Antes de gerar tráfego sintético, extraímos **distribuições estatísticas** dos dados reais do Sprint 1:

| O que extrair | De onde | Onde armazenar |
|---|---|---|
| Distribuição de duração de sessões legítimas | `sessions.parquet` (rótulo BENIGN) | `synth/distributions/session_duration.json` |
| Distribuição de requisições por sessão | idem | `synth/distributions/session_requests.json` |
| Distribuição de JA4 entre usuários legítimos | idem | `synth/distributions/ja4_users.json` |
| Distribuição de endpoints visitados | idem | `synth/distributions/endpoints.json` |
| Distribuição temporal de chegada de sessões | idem | `synth/distributions/arrival.json` |

A geração de tráfego legítimo amostra dessas distribuições; ataque é injetado seguindo os parâmetros de cada cenário.

## Parâmetros do gerador

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `K` | int | 1 | Número de origens distintas coordenadas |
| `legitimate_sessions` | int | 500 | Sessões legítimas concorrentes |
| `attack_variant` | enum | `slowloris` | `slowloris`, `slow_body`, `slow_read`, `hulk`, `goldeneye` |
| `coordination_ja4_share` | float [0,1] | 1.0 | Fração das $K$ origens que compartilham mesmo JA4 (1.0 = todas idênticas; 0.0 = nenhuma) |
| `coordination_identity_reuse` | float [0,1] | 0.0 | Fração das origens que reutilizam identidade (cookie/token/username) |
| `coordination_temporal_jitter` | float [0,1] | 0.0 | Jitter no padrão temporal (0 = idêntico, 1 = aleatório) |
| `asn_dispersion` | int | 1 | Número de ASNs distintos pelos quais as $K$ origens se espalham |
| `prefix_dispersion` | int | 1 | Número de prefixos /24 distintos |
| `window_s` | int | 300 | Janela temporal da campanha (s) |
| `seed` | int | 42 | Reprodutibilidade |

## Saída

Stream de eventos HTTP estruturados em JSONL (uma linha por requisição), pronto para ingestão pelo *pipeline* do Sprint 1:

```json
{
  "timestamp": "2026-05-30T17:32:18.234Z",
  "src_ip": "192.0.2.42",
  "src_port": 51234,
  "dst_ip": "10.0.0.1",
  "dst_port": 443,
  "tls_ja4": "t13d1516h2_8daaf6152771_b186095e22b6",
  "session_id": "synth_c001_s042",
  "identity_token": null,
  "method": "POST",
  "path": "/api/checkout/payment",
  "headers": {"User-Agent": "slowhttptest/1.8"},
  "status_code": 200,
  "asn": 64500,
  "is_attack": true,
  "campaign_id": "synth_c001"
}
```

Os campos `is_attack` e `campaign_id` são **ground truth** que o pipeline **não vê** (são removidos antes de alimentar o KG). Servem só para avaliação posterior.

## Cenários pré-configurados

| Cenário | $K$ | Descrição | Config |
|---|---|---|---|
| **A — Concentrado** | 1 | Single-source, sem coordenação entre sessões | `configs/scenario_A.yaml` |
| **B — Moderado** | 10, 50, 100 | Botnet pequena, JA4 compartilhado, alguns ASNs | `configs/scenario_B.yaml` |
| **C — Distribuído** | 1000, 10000 | Mirai-style: muitos ASNs, mesma assinatura TLS | `configs/scenario_C.yaml` |

## Como rodar (quando Sprint 1 estiver validado)

```bash
cd experiments/sprint-2

# 1. Calibrar contra os outputs do Sprint 1
make calibrate

# 2. Gerar cenários A, B, C (~1h cada, 30 seeds cada)
make scenario-A
make scenario-B
make scenario-C

# 3. Validar visualmente
make validate
```

Saídas em `$DATA_ROOT/synth/scenarios/{A,B,C}/`, prontas para Sprint 3 (baselines + ablação).

## Gates de aprovação

- [ ] Calibração: distribuições do legítimo sintético dentro de 10% das reais (teste Kolmogorov-Smirnov)
- [ ] Reprodutibilidade: mesma seed → output bit-idêntico
- [ ] Ground truth: campaign_id corresponde aos eventos atacantes da geração
- [ ] Cobertura: 30 seeds por cenário × 5 variantes de ataque = 150 runs em A, B e C

## Próximos passos

1. Validar Sprint 1 (CICIDS2017) — produz `sessions.parquet` com legítimo real
2. Rodar `make calibrate` em Sprint 2 — extrai distribuições
3. Gerar os três cenários
4. Avançar para Sprint 3 (baselines + ablação)
