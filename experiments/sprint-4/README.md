# Sprint 4 — Execução completa + calibração de pesos

> **Objetivo:** transformar o resultado preliminar do Sprint 3 em números
> estatisticamente sólidos (n≥30 seeds, IC bootstrap, testes pareados +
> Bonferroni + Cohen's d) e calibrar os pesos $w_i$ de $\Omega(S)$.

## Como rodar

```bash
make run       # 30 seeds × K∈{50,1000}: ablação a/b/c/d + 3 baselines + testes
make weights   # grid search dos pesos w_i {0.3,0.5,0.7,0.9,1.0}³ + sensibilidade
make figures   # money figure (AUC vs K com IC95%)
```

## Resultados (n=30 seeds, campanhas furtivas distribuídas, cenário realista de mesmo serviço)

ROC AUC [IC95% bootstrap] de detecção de ataque por sessão. Cenário **realista de mesmo
serviço**: usuários legítimos acessam o serviço atacado em `:443`, de modo que **nenhum
atributo por-sessão** (incluindo a porta-alvo) separa benigno de atacante.

Baseline por-sessão **forte** (8–9 *features* de fluxo, não as 3 do baseline magro):

| config | K=50 | K=1000 |
|---|---|---|
| (a) ML por-sessão (forte) | 0.519 | 0.502 |
| (b) ontologia s/ relatedBy | 0.527 | 0.503 |
| (c) só network proximity | 0.523 | 0.664 |
| **(d) arcabouço completo** | **0.968** | **0.976** |
| baselines (Fernandes/Bharathi/Kemp) | ~0.50 | ~0.50 |

**Nota (reauditoria):** com o baseline por-sessão **forte**, o (a) fica no nível do acaso
(0,519 / 0,502) **mesmo com 8–9 features** — confirma que a separação no regime furtivo
não está nas *features* de fluxo por sessão, e sim na estrutura de correlação entre sessões.
No cenário de mesmo serviço, a config **(b)** — ontologia com atributos por-sessão
(identidade, porta-alvo) mas **sem** as relações `relatedBy_*` — também fica **no acaso**
(0,527 / 0,503), junto de (a) e dos baselines da literatura: como benigno e atacante
compartilham o mesmo endpoint `:443`, nenhum atributo por-sessão os distingue. **Só** as
relações explícitas `relatedBy_*` entre sessões (d) separam. É a versão **mais forte** do
resultado: o *gap* (d)−(b) cresceu de ~0,10 para ~0,47, e o efeito **não** pode mais ser
descartado como artefato da porta-alvo.

**Testes pareados (Wilcoxon, Bonferroni, Cohen's d):**

| contraste | p (Bonferroni) | Cohen's d |
|---|---|---|
| **K=1000, (d)−(c)** | **7.4e-09** | **+12.2** |
| **K=1000, (d)−(a)** | **7.4e-09** | **+19.6** |

→ Figura: [`results/money_figure_auc_vs_k.png`](results/money_figure_auc_vs_k.png)

## Gates

- [x] **n≥30 runs/config** concluídos
- [x] **(d)−(c) significativo no Cenário C, p<0.01 após Bonferroni** (p_bonf=7.4e-09, d=12.2) ✅
- [x] Pesos documentados com sensibilidade ±20% — **corroborados no regime realista**

## Calibração de pesos — corroborada no cenário realista de mesmo serviço

No **cenário realista de mesmo serviço** (legítimos acessam o serviço atacado em `:443`),
o *grid search* dos pesos $w_i$ **de-satura e corrobora o esquema**: o melhor vetor é
**(w_tls=1,0, w_endpoint=0,3, w_net=0,3)** — TLS dominante, os demais no mínimo —,
confirmando **empiricamente** que o *fingerprint* TLS deve dominar a ponderação. Os pesos
do paper (1,0 / 0,6 / 0,3) ficam a **0,006 de AUC do ótimo** (0,879 vs 0,885) e são
**robustos a ±20%** (queda máxima de 0,006). Nuance honesta a manter: isso valida a
**ORDEM** dos pesos (TLS ≫ endpoint ≈ rede), **não** seus valores absolutos; a calibração
plena ainda exige dados de produção com sinais parciais/conflitantes. Documentado
em [`results/sprint4_weights.json`](results/sprint4_weights.json).

> **Nota histórica (superada).** Numa versão anterior, num sintético fácil demais, o *grid
> search* parecia saturar (AUC alta para toda combinação) e a calibração foi declarada
> inconclusiva; no cenário realista de mesmo serviço o *grid* de-satura e passa a
> corroborar a ordenação acima.

## Limitações → trabalho futuro

- 2 pontos de K (50, 1000); uma curva mais densa (K∈{10,50,200,1000,10000}) seria
  melhor para a figura.
- (b) fica **no acaso** (~0,50) no cenário de mesmo serviço: como benigno e atacante
  compartilham o endpoint `:443`, nenhum atributo por-sessão (nem a porta-alvo) os
  separa — só as relações `relatedBy_*` de (d) separam. (A versão antiga, em que (b)
  chegava a ~0,88, embutia um artefato sintético: a porta de destino distinguia
  trivialmente ataque de benigno.)
- Calibração de pesos: a **ordem** (TLS dominante) é corroborada no cenário realista de
  mesmo serviço (acima); a calibração dos **valores absolutos** exige dados de produção
  com sinais parciais/conflitantes. Sprint 5 / dados reais (KLAGE).
