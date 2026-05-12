# Índice — Traduções da Literatura em Português

Esta pasta contém traduções integrais dos 11 artigos em [`docs/pdfs/`](../pdfs/) para português, organizadas por prioridade de leitura para o paper [`papers/http-session/article.tex`](../../papers/http-session/article.tex).

## Como usar este índice

- Cada paper tem um arquivo `NN-autor-ano.md` com a tradução integral.
- Para figuras que não consegui extrair, há marcação **`📌 Ver Figura X na página Y do original`** apontando para o PDF original em `docs/pdfs/`.
- Tabelas foram recriadas em Markdown.
- Fórmulas matemáticas foram preservadas em LaTeX inline (`$...$`) ou bloco (`$$...$$`).
- Referências `[1]`, `[2]` etc. mantêm a numeração original de cada paper.

## Prioridade de leitura

### Tier 1 — Leitura obrigatória (citados no Abstract/Intro)

| Ordem | Arquivo | Paper | Tempo estimado |
|---|---|---|---|
| 1 | `01-tripathi-hubballi-2021.md` | Tripathi & Hubballi (2021), ACM CSUR — Survey de Layer 7 DoS | 5 h |
| 2 | `02-odusami-2020.md` | Odusami et al. (2020), IJ Communication Systems — Meta-análise de 75 estudos | 3 h |
| 3 | `03-kemp-2023.md` | Kemp et al. (2023), J. Big Data — Detecção ML para Layer 7 HTTP lento | 1.5 h |
| 4 | `04-liu-2022.md` | Liu et al. (2022), Electronics MDPI — Survey de KG em Cibersegurança | 2 h |

### Tier 2 — Importante (metodologia e posicionamento)

| Ordem | Arquivo | Paper | Tempo estimado |
|---|---|---|---|
| 5 | `05-jia-2018.md` | Jia et al. (2018), Engineering — KG prático para cibersegurança (quintupla) | 1.5 h |
| 6 | `06-bonagiri-2024.md` | Bonagiri et al. (2024), ASIANCON — KG em cibersegurança (CS13K) | 1.5 h |
| 7 | `07-ehrlinger-2016.md` | Ehrlinger & Wöß (2016), SEMANTiCS — Definição de KG | 0.5 h |

### Tier 3 — Baselines (você só precisa saber o que fazem)

| Ordem | Arquivo | Paper | Tempo estimado |
|---|---|---|---|
| 8 | `08-fernandes-2015.md` | Fernandes et al. (2015), Applied Soft Computing — PCA sobre NetFlow | 1 h |
| 9 | `09-bharathi-2012.md` | Bharathi & Sukanesh (2012), WSEAS — PCA + k-means para App-DDoS | 45 min |

### Tier 4 — Opcional (pode pular)

| Ordem | Arquivo | Paper | Motivo |
|---|---|---|---|
| 10 | `10-srivastava-2011.md` | Srivastava et al. (2011), PDCTA — Survey antigo de DDoS | Substituído pelo Tripathi 2021 |
| 11 | `11-moustafa-slay-2015.md` | Moustafa & Slay (2015), MilCIS — Dataset UNSW-NB15 | Não usaremos o dataset |

## Status das traduções

- [x] `00-indice.md` (este arquivo)
- [x] `01-tripathi-hubballi-2021.md`
- [x] `02-odusami-2020.md`
- [x] `03-kemp-2023.md`
- [x] `04-liu-2022.md`
- [x] `05-jia-2018.md`
- [x] `06-bonagiri-2024.md`
- [x] `07-ehrlinger-2016.md` *(proof-of-concept — validar formato)*
- [x] `08-fernandes-2015.md`
- [x] `09-bharathi-2012.md`
- [x] `10-srivastava-2011.md`
- [x] `11-moustafa-slay-2015.md`

## Mapeamento por tópico

| Tópico | Papers principais |
|---|---|
| Estatísticas de DDoS Layer 7 (motivação) | 01-Tripathi, 02-Odusami |
| Taxonomia de ataques HTTP/DNS Camada 7 | 01-Tripathi |
| Meta-análise de métodos de detecção | 02-Odusami |
| Lacuna de KG em segurança operacional | 04-Liu |
| Construção de KG em cibersegurança | 05-Jia, 06-Bonagiri |
| Definição formal de KG | 07-Ehrlinger |
| Baseline ML moderno para HTTP Slow | 03-Kemp |
| Baseline estatístico (perfilamento PCA) | 08-Fernandes |
| Baseline comportamental | 09-Bharathi |
| Datasets de NIDS | 11-Moustafa (UNSW-NB15) |
