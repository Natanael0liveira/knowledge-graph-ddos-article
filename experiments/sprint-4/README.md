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

## Resultados (n=30 seeds, campanhas furtivas distribuídas)

ROC AUC [IC95% bootstrap] de detecção de ataque por sessão:

| config | K=50 | K=1000 |
|---|---|---|
| (a) ML por-sessão | 0.524 [0.511, 0.536] | 0.549 [0.545, 0.553] |
| (b) ontologia s/ relatedBy | 0.888 [0.878, 0.896] | 0.905 [0.902, 0.907] |
| (c) só network proximity | 0.558 [0.531, 0.589] | 0.738 [0.709, 0.770] |
| **(d) arcabouço completo** | **1.000 [1.000, 1.000]** | **1.000 [0.999, 1.000]** |
| baseline Fernandes 2015 | 0.491 | 0.493 |
| baseline Bharathi 2012 | 0.487 | 0.490 |
| baseline Kemp 2023 | 0.523 | 0.545 |

**Testes pareados (Wilcoxon, Bonferroni n=4, Cohen's d):**

| contraste | Δ | p (Bonferroni) | Cohen's d |
|---|---|---|---|
| K=50, (d)−(c) | +0.442 | 7.5e-09 | +5.14 |
| K=50, (d)−(a) | +0.476 | 7.5e-09 | +12.95 |
| **K=1000, (d)−(c)** | **+0.262** | **2.2e-05** | **+2.91** |
| K=1000, (d)−(a) | +0.451 | 7.5e-09 | +36.35 |

→ Figura: [`results/money_figure_auc_vs_k.png`](results/money_figure_auc_vs_k.png)

## Gates

- [x] **n≥30 runs/config** concluídos
- [x] **(d)−(c) significativo no Cenário C, p<0.01 após Bonferroni** (p=2.2e-05) ✅
- [x] Pesos documentados com sensibilidade ±20% — **mas ver caveat**

## Calibração de pesos — caveat honesto

O grid search dos pesos $w_i \in \{0.3,0.5,0.7,0.9,1.0\}^3$ retorna **AUC=1.0 para
TODA combinação** (inclusive os pesos do paper 1.0/0.6/0.3), robusto a ±20%. Isso
**não** significa que os pesos são ótimos — significa que o sintético é fácil demais
para *discriminar* pesos: a separação attack-dominante vs benigno no nível de cluster
está saturada. Calibração significativa de $w_i$ exige um conjunto de validação mais
difícil (tráfego real, ou sintético com sinais parciais que se compensem). Documentado
em [`results/sprint4_weights.json`](results/sprint4_weights.json).

## Limitações → trabalho futuro

- 2 pontos de K (50, 1000); uma curva mais densa (K∈{10,50,200,1000,10000}) seria
  melhor para a figura.
- (b) ≈ 0.9 porque inclui `dst_port` (convergência de endpoint vaza como atributo
  por-sessão); (d) ainda a supera.
- Pesos não-calibráveis no sintético (acima). Sprint 5 / dados reais (KLAGE).
