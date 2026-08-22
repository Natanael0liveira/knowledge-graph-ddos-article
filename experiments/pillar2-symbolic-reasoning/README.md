# Pilar 2 — Raciocínio Simbólico Nativo (veredicto-como-derivação)

> Contribuição 2 do paper, antes **não codificada**. A regra `coordinatedHTTPFlood`
> é avaliada por **soma ponderada das sub-relações** `relatedBy_*`, e o veredicto é a
> **derivação** que satisfez a regra — não a saída de um classificador.

## Desenho (honesto sobre SWRL × SPARQL)

| Etapa | Linguagem | O quê |
|---|---|---|
| 1. Instanciar `relatedBy_*` par-a-par | **SWRL** (regras de Horn) | "se ?a e ?b compartilham JA4 → relatedByTLSFingerprint(?a,?b)" |
| 2. Agregação Ω(S) = Σ w_i·\|pares_i\| ≥ τ | **SPARQL** | SWRL não agrega; SPARQL soma, com os pesos lidos da ontologia |

As regras SWRL formais estão em [`rules/relatedBy.swrl`](rules/relatedBy.swrl). Como
o rdflib não tem reasoner SWRL nativo (e essas regras são CONSTRUCTs), a etapa 1 é
executada como SPARQL CONSTRUCT — **semanticamente equivalente** às regras de Horn.

Os pesos `w_i` são lidos de `coordinationWeight` na ontologia (`ddos_ontology.owl`) —
**nada hard-coded**: a ponderação é governada pela ontologia.

## Demonstração (offline)

```bash
make demo
```

```
Pesos (da ontologia): TLS=1.0 ... NetworkProximity=0.3
Arestas materializadas: relatedByTLSFingerprint=10, relatedByEndpointConvergence=28, NetworkProximity=0
▶ REGRA DISPARADA: coordinatedHTTPFlood @ 10.0.0.1_443
  Ω(S) = 26.8 ≥ τ=5.0   (|S|=8)
  DERIVAÇÃO:
    relatedByTLSFingerprint        10 pares × 1.0 = 10.0
    relatedByEndpointConvergence   28 pares × 0.6 = 16.8
  veredicto = a derivação acima (não um score)
```

## A regra avaliada COMO detector (Sprint 6)

Todo número de detecção do paper vinha de um classificador sobre features, o que mede
a **representação** e não diz nada sobre esta camada. O Sprint 6 avaliou a regra ponta
a ponta: as sessões que casam com o escopo derivado **são** o conjunto marcado, sem
treino e sem limiar. E, para ser justo, o classificador foi forçado ao **mesmo ponto de
operação**:

| cenário | regra: recall / FPR / F1 | RF AUC | RF recall @ FPR=0 |
|---|---|---|---|
| monolítico (M=1) | 84,0% / 0,00% / 0,885 | 0,997 | **91,7%** |
| M=5 | 90,0% / 0,00% / 0,948 | 0,996 | 88,6% |
| M=25 | 90,3% / 0,00% / **0,949** | 0,979 | **36,4%** |
| M=100 | 85,0% / 0,00% / 0,919 | 0,961 | **17,6%** |
| M=25, adversarial | 30,4% / 3,78% / 0,452 | 0,862 | **7,8%** |

**Não é vitória uniforme.** No regime monolítico o RF empata ou ganha — não há vantagem
simbólica ali. A partir de 25 stacks a ordem inverte de forma acentuada. O que a AUC
esconde é isso: 0,979 corresponde a recuperar **um terço** do ataque a falso positivo
zero, porque a distribuição de escores se sobrepõe ao benigno na cauda. A regra não
produz escore para limiarizar — produz um conjunto definido por teste de enriquecimento
contra fundo explícito, e por isso o FPR é 0,00% **por construção, não por ajuste**.

Ver [`../sprint-6-noms/scripts/symbolic_detector.py`](../sprint-6-noms/scripts/symbolic_detector.py).

## Como compõe com o Pilar 4

O cluster (sessões no mesmo endpoint) inclui benignos — a convergência de endpoint
sozinha não discrimina. O sinal forte (TLS: 10 pares só entre atacantes) é o que o
[Pilar 4](../pillar4-evidence-mitigation/) usa para derivar o escopo cirúrgico
`(tlsJa4, endpoint)` e separar atacantes de legítimos com dano colateral ~0.

Fluxo completo: **detecção (G3/G4) → raciocínio simbólico (Pilar 2, esta pasta) →
evidência + mitigação (Pilar 4)**.

## Caveats honestos

- Demo em grafo-brinquedo; rodar sobre o KG real precisa do HD (carregar sessões reais).
- Etapa SWRL executada como SPARQL CONSTRUCT (equivalente p/ regras de Horn); um
  reasoner SWRL/OWL formal (ex.: owlready2+Pellet) exigiria Java e não muda a semântica.
- Sub-relações Temporal/Payload omitidas (sem dado a nível de sessão — ver ablação).
- O cluster aqui = "mesmo endpoint"; refinar a definição de S é trabalho fino.
