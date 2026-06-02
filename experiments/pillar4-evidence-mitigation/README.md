# Pilar 4 — Cadeia de Evidência Simbólica + Mitigação Cirúrgica

> Contribuição 4 do paper, antes **não codificada**. Quando a regra
> `coordinatedHTTPFlood` dispara sobre um cluster S, este módulo acopla
> **detecção → evidência simbólica → mitigação de escopo derivado**.

## O que faz (`scripts/evidence_mitigation.py`)

1. **Decompõe Ω(S)** por sub-relação `relatedBy_*` (quais sinais ativaram, com peso).
2. **Deriva o escopo de mitigação** do conjunto mínimo de propriedades que o cluster
   compartilha (≥90% de cobertura) — prioriza sinais de peso alto (JA4) sobre baixo
   (/24). Tipicamente `(tlsJa4, endpoint)`, reforçado por `/24` só se o botnet for
   concentrado.
3. **Exporta a cadeia de evidência** em **JSON-LD** (vocabulário da ontologia:
   `kg:CoordinatedHTTPFlood`, `kg:activatedSubRelations`, `kg:coordinationWeight`,
   `kg:derivedMitigationScope`) e em **STIX 2.1** (`indicator` + `course-of-action` +
   `relationship` *mitigates*). O veredicto É a derivação que satisfez a regra.
4. **Estima o dano colateral** do escopo cirúrgico vs um rate-limit GLOBAL no endpoint.

## Demonstração (offline, sem HD)

```bash
make demo      # cluster-brinquedo: 12 atacantes furtivos + 400 benignos no mesmo endpoint
```

Resultado:

```
Ω(S) = 105.6  (12 sessões)
  relatedByTLSFingerprint        pares=66  ×1.0 = 66.0
  relatedByEndpointConvergence   pares=66  ×0.6 = 39.6   (NetworkProximity NÃO ativa — /24 dispersos)
ESCOPO DERIVADO: {tlsJa4: t13d_botnetX, endpoint: 10.0.0.1:443}
DANO COLATERAL (400 BENIGN):
  cirúrgica (escopo derivado): 0   (0.00%)
  rate-limit GLOBAL endpoint:  198 (49.50%)
  → redução de dano colateral: 100.0%
```

Saídas em `--out-dir`: `evidence.jsonld`, `mitigation.stix.json`.

## Como ligar aos dados reais (próxima sessão online)

O cluster de entrada é uma fatia das sessões que a `coordinatedHTTPFlood` (G4)
detectou. Fluxo: `compute_coordination.py` marca o `det_cluster` campeão → passar
essas sessões + um conjunto BENIGN como `--cluster`/`--benign`.

## Caveats honestos

- **Demonstrado em cluster-brinquedo**; rodar sobre um cluster REAL detectado precisa
  do HD (parquets). A lógica está validada, os números reais virão depois.
- O **STIX 2.1 é representativo** (estrutura correta: bundle/indicator/CoA/relationship,
  `pattern_type: stix`), não validado contra um validador STIX formal. JA4 usa uma
  extensão custom `x-tls:ja4`.
- Só as 3 sub-relações com dado a nível de sessão entram na decomposição (mesmo escopo
  da ablação): TLS/JA4, endpoint, /24.
- O escopo é derivado por cobertura modal (≥90%); calibrar esse limiar é trabalho fino.
