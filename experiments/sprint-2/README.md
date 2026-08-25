# Sprint 2 — Calibrated synthetic generator

Generate traffic parameterized by the degree of distribution K, calibrated
against the real distributions extracted in Sprint 1, so that Scenarios A
(concentrated, K = 1), B (moderate, K = 10–100) and C (distributed, K ≥ 1000)
can be evaluated.

**Status:** implemented and calibrated against CICIDS2017. Generates A/B/C and
the **realistic same-service scenario** (legitimate users on the attacked `:443`),
which is the canonical one reported in the paper. KS fidelity verified
(D = 0.003 duration, 0.002 request count).

## Why synthetic traffic is necessary

The cluster ground truth needed for per-campaign recall, and for the ablation of
(c) `relatedByNetworkProximity` only against (d) the full family, **does not exist
in public datasets**. CICIDS2017 labels are per flow, not per coordinated
campaign. The generator gives each run a campaign with perfectly known ground
truth, a controlled K, and calibration against real data so realism is not
asserted.

## Calibration principle

Statistical distributions are extracted from Sprint 1 output before any traffic
is generated:

| Distribution | Source | Stored at |
|---|---|---|
| Legitimate session duration | `sessions.parquet` (BENIGN) | `synth/distributions/session_duration.json` |
| Requests per session | same | `synth/distributions/session_requests.json` |
| JA4 across legitimate users | same | `synth/distributions/ja4_users.json` |
| Endpoints visited | same | `synth/distributions/endpoints.json` |
| Session arrival times | same | `synth/distributions/arrival.json` |
| Bytes and packets per request (fwd/bwd) | same | `synth/distributions/flow_*.json` |

The **per-request flow distributions** are what make stealthy attacker sessions
mimetic in volume and timing as well. They are the reason a **strong** per-session
baseline with 8–9 features sits at chance, rather than a weakened adversary.

## Generator parameters

| Parameter | Default | Meaning |
|---|---|---|
| `K` | 1 | Number of distinct coordinated origins |
| `legitimate_sessions` | 500 | Concurrent legitimate sessions |
| `attack_variant` | `slowloris` | `slowloris`, `slow_body`, `slow_read`, `hulk`, `goldeneye` |
| `coordination_ja4_share` | 1.0 | Fraction of the K origins sharing one JA4 |
| `coordination_identity_reuse` | 0.0 | Fraction reusing an identity (cookie, token, username) |
| `coordination_temporal_jitter` | 0.0 | Jitter in the temporal pattern (0 identical, 1 random) |
| `asn_dispersion` | 1 | Distinct ASNs the origins spread across |
| `prefix_dispersion` | 1 | Distinct /24 prefixes |
| `benign_same_service` | false | If true, legitimate users hit the **same** service and port under attack. **The canonical realistic scenario**; removes the port artifact that inflated configuration (b) |
| `benign_ja4_pool` | inherited | Distinct JA4 in legitimate traffic (2000 in the realistic scenario) |
| `benign_ja4_zipf_alpha` | 0 (uniform) | Shape of benign JA4 popularity. Uniform is unrealistic: the production measurement has a 38.4% head. Canonical: 1.5 |
| `botnet_ja4_stacks` | 1 | Distinct TLS stacks in the botnet. 1 is monolithic and unrealistic; canonical: 25 |
| `botnet_ja4_adversarial` | false | If true, the botnet adopts the **most common benign** fingerprints instead of its own namespace |
| `window_s` | 300 | Campaign window, seconds |
| `seed` | 42 | Reproducibility |

The last three were added in Sprint 6 and are what make the scenario resemble
production.

## Output

Structured HTTP events as JSONL, one line per request, ready for the Sprint 1
pipeline:

```json
{
  "timestamp": "2026-05-30T17:32:18.234Z",
  "src_ip": "192.0.2.42", "src_port": 51234,
  "dst_ip": "10.0.0.1", "dst_port": 443,
  "tls_ja4": "t13d1516h2_8daaf6152771_b186095e22b6",
  "session_id": "synth_c001_s042", "identity_token": null,
  "method": "POST", "path": "/api/checkout/payment",
  "headers": {"User-Agent": "slowhttptest/1.8"},
  "status_code": 200, "asn": 64500,
  "is_attack": true, "campaign_id": "synth_c001"
}
```

`is_attack` and `campaign_id` are **ground truth that the pipeline never sees**;
they are stripped before the KG is fed and exist only for evaluation.

## Running

```bash
make calibrate     # extract distributions from Sprint 1 output
make scenario-A    # ~1 h each, 30 seeds each
make scenario-B
make scenario-C
make validate
```

Scenario configs are in `configs/scenario_{A,B,C}.yaml`; output lands in
`$DATA_ROOT/synth/scenarios/{A,B,C}/` for Sprint 3.

## Acceptance gates

- [x] Calibration: synthetic legitimate close to real (KS D = 0.003 duration,
      0.002 request count; `results/ks_validation.json`)
- [ ] Reproducibility: same seed, bit-identical output
- [ ] Ground truth: `campaign_id` matches the generated attacker events
- [ ] Coverage: 30 seeds × 5 attack variants across A, B and C
