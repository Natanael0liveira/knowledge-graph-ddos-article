# Artigo NOMS — versão em português

Tradução fiel de [`../http-session-noms/`](../http-session-noms/), mesmo formato
IEEEtran de duas colunas, mesmos números, mesmas figuras.

**Esta não é a versão de submissão.** O NOMS exige inglês. Use
`../http-session-noms/article.pdf` para submeter. Esta cópia existe para leitura,
revisão interna e discussão com quem prefira português.

## O que difere da versão em inglês

| | inglês (submissão) | português (esta) |
|---|---|---|
| páginas | 11 (corpo 8, refs 9, apêndices 9–11) | 12 (corpo ~9, refs 9–10, apêndices 10–12) |
| babel | — | `\usepackage[brazilian]{babel}` |
| decimais | ponto (`0.982`) | vírgula (`0{,}982`) |
| figuras | rótulos em inglês | **mesmas figuras, rótulos em inglês** |

O texto em português corre 15–20% mais longo, então o limite de 8 páginas de corpo
do NOMS não se aplica aqui e não foi perseguido — comprimir custaria conteúdo sem
ganho nenhum, já que esta cópia não vai para a submissão. Ainda assim cabe nas 12
páginas totais.

As figuras são cópias binárias das da versão em inglês e portanto mantêm rótulos
em inglês. Para gerá-las em português, adapte as *strings* de
`../http-session-noms/figures/make_figures_en.py`.

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
