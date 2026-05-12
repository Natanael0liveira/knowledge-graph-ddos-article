# Índice — Traduções da Literatura em Português

Esta pasta contém traduções integrais dos 11 artigos em [`docs/pdfs/`](../pdfs/) para português, com **ordem de leitura recomendada** para o paper [`papers/http-session/article.tex`](../../papers/http-session/article.tex).

## Esclarecimento importante sobre tiering

**Todas as referências citadas no `\cite{}` do artigo são obrigatórias** — não há referência "opcional" no sentido de descartável. A tiering abaixo é sobre **ordem de leitura** e **profundidade de leitura**, não sobre necessidade de citação.

| Tier | Significado prático |
|---|---|
| **Tier 1** — *Leia primeiro, leia inteiro* | Esses 4 papers moldam toda a narrativa do nosso paper. Citamos pesadamente. Você precisa conhecer profundamente. |
| **Tier 2** — *Leia depois, leia partes-chave* | Fundamento e metodologia. Citamos em pontos específicos. Você precisa entender as ideias centrais. |
| **Tier 3** — *Saiba o que fazem, leia se sobrar tempo* | Baselines de comparação. Citamos para defender que "fizemos comparação justa". Você só precisa saber **o algoritmo** que cada um usa. |
| **Tier 4** — *Pode pular, está no índice por completude* | Substituídos por papers mais recentes ou fora do escopo. Não citamos no artigo atual. Mantemos a tradução por completude. |

## Como usar este índice

- Cada paper tem um arquivo `NN-autor-ano.md` com a tradução integral.
- Para figuras que não consegui extrair, há marcação **`📌 Ver Figura X na página Y do original`** apontando para o PDF original em `docs/pdfs/`.
- Tabelas foram recriadas em Markdown.
- Fórmulas matemáticas foram preservadas em LaTeX inline (`$...$`) ou bloco (`$$...$$`).
- Referências `[1]`, `[2]` etc. mantêm a numeração original de cada paper.
- Cada tradução termina com uma seção **"Pontos-chave para o nosso paper"** com anotação minha sobre como usar a leitura na hora de escrever.

## Ordem de leitura recomendada

### Tier 1 — Leia primeiro, leia inteiro (4 papers, ~11.5 h)

| Ordem | Arquivo | Paper | Tempo | Citado em |
|---|---|---|---|---|
| 1 | [`01-tripathi-hubballi-2021.md`](01-tripathi-hubballi-2021.md) | Tripathi & Hubballi (2021), ACM CSUR — Survey de Layer 7 DoS | 5 h | Abstract, §1.1, §1.2 |
| 2 | [`02-odusami-2020.md`](02-odusami-2020.md) | Odusami et al. (2020), IJ Communication Systems — Meta-análise de 75 estudos | 3 h | Abstract, §1.1, §1.2 (gap 1) |
| 3 | [`03-kemp-2023.md`](03-kemp-2023.md) | Kemp et al. (2023), J. Big Data — Detecção ML para Layer 7 HTTP lento | 1.5 h | §1.1, §1.2 (gap 2), §1.4, §4.4 (baseline) |
| 4 | [`04-liu-2022.md`](04-liu-2022.md) | Liu et al. (2022), Electronics MDPI — Survey de KG em Cibersegurança | 2 h | §1.2 (gap 3) — *quote literal* |

### Tier 2 — Leia depois, leia partes-chave (3 papers, ~3.5 h)

| Ordem | Arquivo | Paper | Tempo | Citado em |
|---|---|---|---|---|
| 5 | [`05-jia-2018.md`](05-jia-2018.md) | Jia et al. (2018), Engineering — KG prático para cibersegurança (modelo quintupla) | 1.5 h | §1.2 (gap 3), §1.4 (contribuição 2) |
| 6 | [`06-bonagiri-2024.md`](06-bonagiri-2024.md) | Bonagiri et al. (2024), ASIANCON — KG em cibersegurança (CS13K) | 1.5 h | §1.2 (gap 3), §1.4 (contribuição 2) |
| 7 | [`07-ehrlinger-2016.md`](07-ehrlinger-2016.md) | Ehrlinger & Wöß (2016), SEMANTiCS — Definição canônica de KG | 0.5 h | Não citado *ainda* — útil quando desenvolvermos §3.2 |

### Tier 3 — Saiba o algoritmo, leia se sobrar tempo (2 papers, ~1.75 h)

| Ordem | Arquivo | Paper | Tempo | Citado em |
|---|---|---|---|---|
| 8 | [`08-fernandes-2015.md`](08-fernandes-2015.md) | Fernandes et al. (2015), Applied Soft Computing — **PCA sobre NetFlow** | 1 h | §1.1, §1.4 (contribuição 3), §4.4 (baseline) |
| 9 | [`09-bharathi-2012.md`](09-bharathi-2012.md) | Bharathi & Sukanesh (2012), WSEAS — **PCA + k-means para App-DDoS** | 45 min | §1.1, §1.4 (contribuição 3), §4.4 (baseline) |

> Para Tier 3, o suficiente é entender o **algoritmo central** que cada um usa. Veja a seção abaixo onde explico **PCA + k-means**. Com isso você consegue defender no paper sem ter que ler os 23 papers inteiros.

### Tier 4 — Pode pular, está aqui por completude (2 papers)

| Ordem | Arquivo | Paper | Motivo de não citar |
|---|---|---|---|
| 10 | [`10-srivastava-2011.md`](10-srivastava-2011.md) | Srivastava et al. (2011), PDCTA — Survey antigo de DDoS | Substituído por Tripathi 2021 (mais recente, mais abrangente) |
| 11 | [`11-moustafa-slay-2015.md`](11-moustafa-slay-2015.md) | Moustafa & Slay (2015), MilCIS — Dataset UNSW-NB15 | Não usaremos este dataset (focamos em geração sintética para cenários A/B/C) |

## Status das traduções

- [x] `00-indice.md` (este arquivo)
- [x] `01-tripathi-hubballi-2021.md`
- [x] `02-odusami-2020.md`
- [x] `03-kemp-2023.md`
- [x] `04-liu-2022.md`
- [x] `05-jia-2018.md`
- [x] `06-bonagiri-2024.md`
- [x] `07-ehrlinger-2016.md`
- [x] `08-fernandes-2015.md`
- [x] `09-bharathi-2012.md`
- [x] `10-srivastava-2011.md`
- [x] `11-moustafa-slay-2015.md`

## Mapeamento das 8 citações ativas do nosso paper

| Citação `.tex` | Tradução | Tier | O que usamos dela |
|---|---|---|---|
| `\cite{tripathi2021application}` | [01](01-tripathi-hubballi-2021.md) | 1 | "292.000 req/s por 13 dias"; "dobra a cada trimestre"; taxonomia de Layer 7 DoS |
| `\cite{odusami2020survey}` | [02](02-odusami-2020.md) | 1 | "47% usam features de sessão"; "4% implementados"; "0 estudos com KG"; "86/90/93% incidência" |
| `\cite{kemp2023approach}` | [03](03-kemp-2023.md) | 1 | Admissão "não validado em tempo real"; baseline ML moderno |
| `\cite{liu2022recent}` | [04](04-liu-2022.md) | 1 | Quote literal sobre KG como corpus vs runtime; survey de aplicações |
| `\cite{jia2018practical}` | [05](05-jia-2018.md) | 2 | Modelo quintupla de KG; KG construído de texto (não de eventos) |
| `\cite{bonagiri2024practical}` | [06](06-bonagiri-2024.md) | 2 | KG mais recente do estado-da-arte; CS13K como ponto de comparação |
| `\cite{fernandes2015autonomous}` | [08](08-fernandes-2015.md) | 3 | Baseline estatístico (PCA sobre NetFlow); features agregadas |
| `\cite{bharathi2012pca}` | [09](09-bharathi-2012.md) | 3 | Baseline comportamental (PCA + k-means); sessão como vetor |

## Mapeamento por tópico

| Tópico | Papers principais |
|---|---|
| Estatísticas de DDoS Layer 7 (motivação) | 01-Tripathi, 02-Odusami |
| Taxonomia de ataques HTTP de Camada 7 | 01-Tripathi |
| Meta-análise de métodos de detecção | 02-Odusami |
| Lacuna de KG em segurança operacional | 04-Liu |
| Construção de KG em cibersegurança | 05-Jia, 06-Bonagiri |
| Definição formal de KG | 07-Ehrlinger |
| Baseline ML moderno para HTTP Slow | 03-Kemp |
| Baseline estatístico (perfilamento PCA) | 08-Fernandes |
| Baseline comportamental (PCA + k-means) | 09-Bharathi |
| Datasets de NIDS (não usaremos) | 11-Moustafa (UNSW-NB15) |

## Referências citadas no paper CDN-Crosssurface (engavetado) ainda sem tradução

Estes papers estão no `references.bib` mas não temos PDF nem tradução. **Não impactam o paper http-session ativo.** Vamos traduzir quando retomarmos o paper CDN.

| Citação `.bib` | Paper | DOI |
|---|---|---|
| `\cite{vanrijswijk2014dnssec}` | van Rijswijk-Deij et al. (2014) — DNSSEC and Its Potential for DDoS | [10.1145/2663716.2663731](https://doi.org/10.1145/2663716.2663731) |
| `\cite{anagnostopoulos2013dns}` | Anagnostopoulos et al. (2013) — DNS Amplification Attack Detection in a Cloud Environment | [10.1109/CLOUD.2013.44](https://doi.org/10.1109/CLOUD.2013.44) |
| `\cite{moura2016anycast}` | Moura et al. (2016) — Anycast and DNS: A Study of Load Balancing and Resilience | [10.1145/2987443.2987446](https://doi.org/10.1145/2987443.2987446) |
| `\cite{pappas2009dns}` | Pappas et al. (2009) — Impact of Configuration Errors on DNS Robustness | [10.1145/1592568.1592604](https://doi.org/10.1145/1592568.1592604) |
