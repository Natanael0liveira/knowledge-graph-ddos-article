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

Baseline por-sessão **forte** (8–9 *features* de fluxo, não as 3 do baseline magro):

| config | K=50 | K=1000 |
|---|---|---|
| (a) ML por-sessão (forte) | 0.505 | 0.498 |
| (b) ontologia s/ relatedBy | 0.877 | 0.893 |
| (c) só network proximity | 0.502 | 0.678 |
| **(d) arcabouço completo** | **0.969** | **0.992** |
| baselines (Fernandes/Bharathi/Kemp) | ~0.50 | ~0.50 |

**Nota (reauditoria):** com o baseline por-sessão **forte**, o (a) fica no nível do acaso
(0,505 / 0,498) **mesmo com 8–9 features** — confirma que a separação no regime furtivo
não está nas *features* de fluxo por sessão, e sim na estrutura de correlação entre sessões.

**Testes pareados (Wilcoxon, Bonferroni, Cohen's d):**

| contraste | p (Bonferroni) | Cohen's d |
|---|---|---|
| **K=1000, (d)−(c)** | **7.4e-09** | **+14.1** |
| **K=1000, (d)−(a)** | **7.4e-09** | **+22.1** |

→ Figura: [`results/money_figure_auc_vs_k.png`](results/money_figure_auc_vs_k.png)

## Gates

- [x] **n≥30 runs/config** concluídos
- [x] **(d)−(c) significativo no Cenário C, p<0.01 após Bonferroni** (p_bonf=7.4e-09, d=14.1) ✅
- [x] Pesos documentados com sensibilidade ±20% — **mas ver caveat**

## Calibração de pesos — caveat honesto

O grid search dos pesos $w_i \in \{0.3,0.5,0.7,0.9,1.0\}^3$ satura (AUC alta para
praticamente toda combinação, inclusive os pesos do paper 1.0/0.6/0.3, robusto a ±20%). Isso
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
