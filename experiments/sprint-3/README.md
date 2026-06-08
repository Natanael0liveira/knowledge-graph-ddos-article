# Sprint 3 — Baselines + Ablação

> **Objetivo:** medir, sobre o **mesmo input**, três *baselines* acadêmicos e quatro
> configurações de ablação (a/b/c/d), isolando a contribuição da família
> `relatedBy_*`. O resultado decisivo aparece nos cenários **furtivos** do Sprint 2.

## As quatro configurações de ablação

Diferem **apenas** no conjunto de features dado a um classificador comum (RandomForest):

| Config | Features | O que testa |
|---|---|---|
| **(a)** ML sem ontologia | fluxo por-sessão **forte** (8–9 features de fluxo) | estado-da-arte por-sessão |
| **(b)** ontologia sem `relatedBy_*` | (a) + atributos ontológicos por-sessão (identidade, alvo) | ontologia sem correlação entre sessões |
| **(c)** só `relatedByNetworkProximity` | (a) + `share_net` (/24) | só o sinal de rede (peso 0.3) |
| **(d)** arcabouço completo | (a) + `share_ja4` + `share_net` + `cluster_size` | família `relatedBy_*` completa |

Os 3 *baselines* (Fernandes 2015 PCA+limiar; Bharathi 2012 k-means; Kemp 2023 RF+SVM)
rodam sobre as features de (a) — são por-sessão por construção.

## Resultado (cenários FURTIVOS do Sprint 2)

Ataque mimético: cada sessão é individualmente indistinguível de um usuário
legítimo; só a estrutura de correlação entre sessões trai a campanha. Números
**canônicos** (n=30 seeds, baseline por-sessão **forte** de 8–9 features, **cenário
realista de mesmo serviço** — legítimos acessam o `:443` atacado; rigor estatístico
e IC no Sprint 4):

| config | K=50 | K=1000 |
|---|---|---|
| (a) ML por-sessão (forte) | 0.519 | 0.502 |
| (b) ontologia s/ relatedBy | 0.527 | 0.503 |
| (c) só network proximity | 0.523 | 0.664 |
| **(d) completo** | **0.968** | **0.976** |
| baselines (Fernandes/Bharathi/Kemp) | ~0.52 | ~0.50 |

**Leitura:** o ML por-sessão **forte**, os baselines **e** a ontologia sem `relatedBy` (b)
ficam todos ~no acaso (0,5) contra campanhas furtivas distribuídas **mesmo com 8–9 features
de fluxo** — atributos ontológicos por-sessão não bastam; é a relação **entre** sessões que
carrega a detecção. O arcabouço completo (d) detecta quase perfeitamente. Em K=50 a
proximidade de rede é fraca (botnet espalhado), mas o JA4 compartilhado (peso 1.0) em (d)
carrega — validando empiricamente a ponderação por resistência-à-evasão do paper.

> **Nota (artefato removido):** numa versão anterior, (b) marcava ~0,88 por um **artefato de
> porta** — o benigno sintético tinha `dst_port` diverso enquanto o ataque ia a `:443`.
> Forçando os legítimos ao **mesmo serviço** (`benign_same_service=true`), o artefato some e
> (b) cai ao acaso: é o cenário realista que o paper reporta.

⚠️ **Caveat:** ataques NÃO-furtivos (slowloris/hulk com assinatura de fluxo distinta)
são separáveis já por (a) — o ganho do raciocínio entre sessões só é grande no regime furtivo.
Em cenário concentrado (K=1) não há campanha (1 sessão), logo ROC é indefinido.

## Como rodar

```bash
# Pré-requisito: Sprint 2 calibrado (make -C ../sprint-2 calibrate)
make scenarios   # gera cenários furtivos K=1/50/1000 (seed 7) + converte p/ sessions
make ablation    # roda baselines + configs a/b/c/d e imprime a tabela
```

## Gates (plano)

- [x] Baselines e config (a) consomem o mesmo input
- [x] (a)–(d) sobre o mesmo input
- [x] Ganho de (d) sobre (a) cresce com K e com furtividade (sanity invertido: em
      ataque não-furtivo todos convergem; em furtivo, (d) ≫ resto)
- [ ] ≥30 seeds + IC bootstrap + testes pareados → **Sprint 4**

## Limitações → Sprint 4

- Resultados preliminares (1 seed). Rigor estatístico (n≥30, bootstrap, Wilcoxon,
  Bonferroni, Cohen's d) é Sprint 4.
- Pesos `w_i` ainda fixos (1.0/0.6/0.3); *grid search* é Sprint 4.
- Baselines são operacionalizações fiéis, não réplicas exatas dos papers.
