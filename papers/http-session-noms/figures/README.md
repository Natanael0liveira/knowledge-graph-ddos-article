# Figuras

Duas categorias, com fluxos de trabalho diferentes. Não misture.

## 1. Esquemas — desenhados no draw.io

Fonte em `src-drawio/*.drawio`, referências de estilo em `reference/`.

| figura | fonte | referência de estilo | estado |
|---|---|---|---|
| `fig1_ontology` | `src-drawio/fig1_ontology.drawio` | `reference/b.pdf` | rascunho — canvas 1032×396, entra a `\textwidth` |
| `fig:rules` (Apêndice A) | — | `reference/modular-symb.pdf` ou `code-frag-4.pdf` | hoje é bloco `verbatim` |
| `fig:chain` (Apêndice D) | — | `reference/table-exec.pdf` | hoje é bloco `verbatim` |
| pipeline de §III-D | — | `reference/mini-framework-6.pdf` | não existe |

**Fluxo:** abrir o `.drawio` em [app.diagrams.net](https://app.diagrams.net) ou no
draw.io desktop → ajustar → *File ▸ Export as ▸ PDF*, com **Crop** ligado e
**Include a copy of my diagram** ligado (assim o `.pdf` volta a ser editável e a
fonte não se perde) → salvar como `figN_nome.pdf` aqui.

### Regra de escala — leia antes de desenhar

O texto encolhe junto com a figura, e é fácil produzir algo ilegível sem
perceber. A figura antiga `fig1_ontology.png` tinha 2100 px incluídos a
`0.72\textwidth`: fator 0,18, corpo de texto a **~5 pt impressos**, abaixo do
piso do IEEE.

Convenção adotada: **desenhe em 2× o tamanho final e inclua com o dobro da
largura.** Para uma figura de largura total (`figure*`), `\textwidth` ≈ 516 pt,
então o canvas é **1032 pt** e as fontes do draw.io saem pela metade:

| fonte no draw.io | impressa |
|---|---|
| 21 pt (título de painel) | 10,5 pt |
| 15 pt (rótulo de nó) | 7,5 pt |
| 13 pt (legenda, anotação) | 6,5 pt |
| 12 pt (rótulo de aresta) | 6 pt |

Nada abaixo de 12 pt no draw.io. Confira o tamanho da página em
*File ▸ Page Setup* antes de exportar.

Depois trocar no `article.tex`: `figures/fig1_ontology.png` → `.pdf`.

### Gramática visual (extraída de `reference/b.pdf`)

- nós em elipse, **sem preenchimento**, traço preto fino (1.2–1.3 pt)
- setas pretas sólidas para relações do modelo
- **cinza tracejado** só para meta-comentário: o que quantifica, anota ou explica
- títulos de painel em negrito, alinhados à esquerda, no topo
- divisor **vertical pontilhado** entre painéis
- Helvetica / Liberation Sans; sem cor decorativa
- proporção larga e baixa (o `b.pdf` é 3:1)

Cor só quando for semântica, nunca para dar ênfase. O `reference/unit-1.pdf` usa
relógio vermelho vs verde porque a cor *é* o resultado; o `b.pdf` não usa cor
nenhuma.

## 2. Gráficos de dados — gerados por código

`fig2_regime`, `fig3_collateral` e `fig4_latency` saem de `make_figures_en.py`,
a partir dos resultados em `experiments/sprint-6-noms/results/`.

**Não redesenhe estes à mão.** O Apêndice E do artigo promete que toda figura
regenera por um comando; desenhá-las converteria número medido em ilustração e
quebraria essa promessa. Para aproximá-las do estilo dos esquemas, mexa no
*matplotlib* — família tipográfica, espessura de traço, paleta — não no
resultado.

```
python make_figures_en.py
```
