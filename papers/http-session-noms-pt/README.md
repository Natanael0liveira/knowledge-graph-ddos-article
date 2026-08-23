# Artigo NOMS — versão em português

Tradução fiel de [`../http-session-noms/`](../http-session-noms/), mesmo formato
IEEEtran de duas colunas, mesmos números, mesmas figuras.

**Esta não é a versão de submissão.** O NOMS exige inglês. Use
`../http-session-noms/article.pdf` para submeter. Esta cópia existe para leitura,
revisão interna e discussão com quem prefira português.

## O que difere da versão em inglês

Nada de conteúdo: todas as correções da versão em inglês foram portadas, incluindo
as de fato (o *d* de Cohen na conclusão, a comparação regra × modelo em M=5, os
ponteiros de apêndice, a promessa de regeneração no Apêndice E) e a numeração
contígua com `Listagem 1-2`.

| | inglês (submissão) | português (esta) |
|---|---|---|
| páginas | 11 (corpo 8, refs 9, apêndices 9–11) | 12 |
| babel | — | `[brazilian]`, com `\figurename` fixado em `Fig.` |
| decimais | ponto (`0.982`) | vírgula (`0{,}982`) |
| blocos de código | `Listing 1-2` | `Listagem 1-2` |
| figuras | rótulos em inglês | **mesmas figuras, rótulos em inglês** |

**Esta não é a versão de submissão.** O NOMS exige inglês e limita o texto
principal a 8 páginas; o português corre 15–20% mais longo e essa restrição não
foi perseguida aqui. Use `../http-session-noms/article.pdf` para submeter.

As figuras são cópias binárias das da versão em inglês e mantêm rótulos em
inglês. Para gerá-las em português, adapte as *strings* de
`../http-session-noms/figures/make_figures_en.py` e o
`src-drawio/fig1_ontology.drawio`.

## Compilar

```
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`IEEEtran.cls`, `IEEEtran.bst` e `references.bib` são cópias das da versão em
inglês; a `.bib` é idêntica, já que as referências são as mesmas.

## Manter em sincronia

Qualquer correção de conteúdo feita na versão em inglês precisa ser replicada
aqui à mão. Não há geração automática — a tradução foi feita por leitura, não por
ferramenta, e um *diff* mecânico não a acompanharia.
