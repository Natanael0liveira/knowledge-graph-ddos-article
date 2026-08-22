# Pilar 4 — Cadeia de Evidência Simbólica + Mitigação Cirúrgica

> Contribuição 4 do paper, antes **não codificada**. Quando a regra
> `coordinatedHTTPFlood` dispara sobre um cluster S, este módulo acopla
> **detecção → evidência simbólica → mitigação de escopo derivado**.

## O que faz (`scripts/evidence_mitigation.py`)

1. **Decompõe Ω(S)** por sub-relação `relatedBy_*` (quais sinais ativaram, com peso).
2. **Deriva o escopo de mitigação.** Duas implementações convivem, de propósito:
   - `derive_scope` — heurística original, pelo JA4 **modal** do subconjunto
     coordenado. **Falha contra botnet heterogênea** (ver abaixo). Mantida para que
     o resultado negativo continue reproduzível.
   - `derive_scope_enriched` — a correção, por **enriquecimento** sobre um perfil
     histórico benigno. É a que o paper usa.
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

> ⚠️ **O número de colateral desta demo (0,00% cirúrgico) é do cenário monolítico.**
> Ele não se sustenta contra botnet heterogênea com a heurística modal — ver a seção
> seguinte.

## O erro que o Sprint 6 encontrou, e a correção

**Escolher por frequência modal está errado por construção.** Frequência premia o que
é comum, e num serviço sob ataque **o que é comum é o tráfego legítimo**. Com a botnet
fragmentada em 5 ou mais stacks TLS, cada stack do atacante fica menor que a cabeça da
distribuição benigna, o modal do cluster passa a ser um fingerprint **legítimo**, e o
escopo derivado vira um filtro que bloqueia:

| cenário (alpha=1,5, benigno realista) | modal: ataque / colateral | enriquecimento |
|---|---|---|
| botnet monolítica (M=1) | 84,0% / 0,00% | 84,0% / 0,00% |
| M=5 | **0,0% / 39,0%** | **90,0% / 0,00%** |
| M=25 | **0,0% / 39,0%** | **90,3% / 0,00%** |
| M=100 | **0,0% / 39,0%** | **85,0% / 0,00%** |
| M=25, adversarial | 3,6% / 39,0% | 30,4% / 3,78% |

Não é degradação suave: o mecanismo seleciona o **alvo errado** e produz um filtro que
só machuca usuários.

**A correção** (`derive_scope_enriched` + `matches_scope_multi`) ordena candidatos por
enriquecimento sobre um perfil histórico de tráfego normal — janela sem ataque, sem uso
de rótulos — e devolve um **conjunto** de fingerprints, que é o que cobre botnet
fragmentada. Ponto de operação: `min_enrichment=3.0`, `min_support=0.01` (0.002 quando
M é elevado; o piso precisa ficar abaixo de 1/M).

Duas condições de contorno, medidas:

- **Adversário que adota a cabeça benigna**: nada fica enriquecido, e a regra recusa
  bloquear os fingerprints populares. Perde-se a vantagem cirúrgica, mas **com
  segurança** — nunca emite o filtro nocivo.
- **Perfil histórico**: tolera desvio moderado (0,45% de colateral com perfil de outra
  distribuição), mas **quebra com perfil plano ou ausente** (81–84%). A qualidade do
  perfil governa a precisão, nunca a cobertura. Mantê-lo é requisito de implantação.

Experimentos e dados em [`../sprint-6-noms/`](../sprint-6-noms/).

> **Nota — toy vs. número canônico do paper.** Este demo-brinquedo dá global 49,5% (só
> ~metade dos 400 benignos cai na janela do cluster). O número **canônico** do paper vem do
> `collateral_eval.py` no **cenário realista de mesmo serviço** (n=30, K=1000), em que os
> legítimos acessam o serviço atacado: aí um *rate-limit* global derruba **100%** dos
> legítimos e o escopo cirúrgico **0%** → redução de 100% (JA4 no escopo em 30/30). É esse
> 0% vs 100% que a §5.5 e a figB reportam.

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
